"""
熔断器 —— 3态 Circuit Breaker

CLOSED  →  正常
  ↓ 连续失败 ≥ threshold (默认 5)
OPEN    →  拒绝请求，计时 recovery_timeout (默认 60s)
  ↓ 超时
HALF_OPEN → 允许一个探测请求
  ↓ 成功 → CLOSED
  ↓ 失败 → OPEN（重新计时）

状态变更时发出 BreakerEvent，供外部观察/日志。

张小龙设计。纯 Python stdlib，无外部依赖。
"""

import threading
import time
import logging
from enum import Enum, auto
from typing import Optional, Callable

logger = logging.getLogger(__name__)


# ── 熔断器状态 ────────────────────────────────────────────────────────────

class BreakerState(Enum):
    """熔断器三态"""
    CLOSED = auto()      # 正常，请求通过
    OPEN = auto()        # 熔断，请求被拒绝
    HALF_OPEN = auto()   # 半开，允许探测请求


# ── 熔断器事件 ────────────────────────────────────────────────────────────

class BreakerEvent:
    """
    熔断器状态变更事件。

    字段:
        breaker_name: 熔断器名称（对应 callback_id 或 tag）
        old_state: 旧状态
        new_state: 新状态
        timestamp: 事件时间戳
        reason: 触发原因描述
        failure_count: 触发时的连续失败计数
    """

    __slots__ = (
        "breaker_name", "old_state", "new_state",
        "timestamp", "reason", "failure_count",
    )

    def __init__(
        self,
        breaker_name: str,
        old_state: BreakerState,
        new_state: BreakerState,
        reason: str,
        failure_count: int,
    ):
        self.breaker_name = breaker_name
        self.old_state = old_state
        self.new_state = new_state
        self.timestamp = time.time()
        self.reason = reason
        self.failure_count = failure_count

    def __repr__(self):
        return (
            f"BreakerEvent({self.breaker_name}: "
            f"{self.old_state.name} → {self.new_state.name} "
            f"@ {self.timestamp:.3f}, reason={self.reason})"
        )


# ── 熔断器监听器 ─────────────────────────────────────────────────────────

# 熔断器状态变更回调
BreakerListener = Callable[[BreakerEvent], None]


# ── 熔断器实现 ────────────────────────────────────────────────────────────

class CircuitBreaker:
    """
    线程安全的熔断器。

    参数:
        name: 熔断器名称
        failure_threshold: 连续失败次数阈值，达到后状态 → OPEN（默认 5）
        recovery_timeout: OPEN 状态维持秒数，超时后 → HALF_OPEN（默认 60.0）
        listener: 可选，状态变更时的回调

    用法:
        cb = CircuitBreaker("my-callback")
        with cb.guard() as ok:
            if ok:
                result = do_something()
                cb.on_success()
            else:
                cb.on_failure()
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        listener: Optional[BreakerListener] = None,
    ):
        self._name = name
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._listener = listener

        self._lock = threading.Lock()
        self._state = BreakerState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._last_state_change_time = time.time()

    # ── 属性 ──────────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def state(self) -> BreakerState:
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    # ── 核心 ──────────────────────────────────────────────────────────────

    def guard(self) -> bool:
        """
        检查是否允许请求通过。

        返回:
            True = 允许执行
            False = 熔断开启，拒绝执行

        注意: 此方法可能触发 HALF_OPEN 状态转换
        （当 OPEN 超时时自动转为 HALF_OPEN）。
        """
        with self._lock:
            if self._state == BreakerState.CLOSED:
                return True

            if self._state == BreakerState.OPEN:
                now = time.time()
                elapsed = now - self._last_state_change_time
                if elapsed >= self._recovery_timeout:
                    # OPEN → HALF_OPEN
                    self._transition_to(
                        BreakerState.HALF_OPEN,
                        reason=f" recovery_timeout({self._recovery_timeout}s) 到期"
                    )
                    return True
                return False

            # HALF_OPEN: 允许探测
            return True

    def on_success(self):
        """报告成功。"""
        with self._lock:
            if self._state == BreakerState.HALF_OPEN:
                self._transition_to(
                    BreakerState.CLOSED,
                    reason="HALF_OPEN 探测成功"
                )
            elif self._state == BreakerState.CLOSED:
                # 重置失败计数
                self._failure_count = 0

    def on_failure(self):
        """报告失败。"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == BreakerState.CLOSED:
                if self._failure_count >= self._failure_threshold:
                    self._transition_to(
                        BreakerState.OPEN,
                        reason=(
                            f"连续失败 {self._failure_count} 次 "
                            f"≥ 阈值 {self._failure_threshold}"
                        )
                    )
            elif self._state == BreakerState.HALF_OPEN:
                # 探测失败，回到 OPEN
                self._transition_to(
                    BreakerState.OPEN,
                    reason="HALF_OPEN 探测失败"
                )

    # ── 重置 ──────────────────────────────────────────────────────────────

    def reset(self):
        """手动重置熔断器到 CLOSED 状态。"""
        with self._lock:
            self._transition_to(
                BreakerState.CLOSED,
                reason="手动重置"
            )
            self._failure_count = 0

    # ── 内部 ──────────────────────────────────────────────────────────────

    def _transition_to(self, new_state: BreakerState, reason: str):
        """执行状态转换，记录日志，触发监听器。"""
        old_state = self._state
        if old_state == new_state:
            return

        self._state = new_state
        self._last_state_change_time = time.time()

        event = BreakerEvent(
            breaker_name=self._name,
            old_state=old_state,
            new_state=new_state,
            reason=reason,
            failure_count=self._failure_count,
        )

        logger.info(
            "熔断器 [%s] %s → %s | 原因: %s | 失败计数: %d",
            self._name, old_state.name, new_state.name,
            reason, self._failure_count,
        )

        # 触发外部监听器
        if self._listener is not None:
            try:
                self._listener(event)
            except Exception as exc:
                logger.error(
                    "熔断器 [%s] 监听器异常: %s", self._name, exc
                )

    def __repr__(self):
        return (
            f"CircuitBreaker(name={self._name!r}, "
            f"state={self._state.name}, "
            f"failures={self._failure_count})"
        )


# ── 熔断器注册表（管理器） ────────────────────────────────────────────────

class BreakerRegistry:
    """
    全局熔断器注册表。
    每个 callback 对应一个熔断器，自动按需创建。
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        callback_id: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        listener: Optional[BreakerListener] = None,
    ) -> CircuitBreaker:
        """获取已有熔断器，或创建新的。"""
        with self._lock:
            if callback_id in self._breakers:
                return self._breakers[callback_id]

            breaker = CircuitBreaker(
                name=callback_id,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                listener=listener,
            )
            self._breakers[callback_id] = breaker
            return breaker

    def get(self, callback_id: str) -> Optional[CircuitBreaker]:
        """获取已有熔断器，不存在返回 None。"""
        with self._lock:
            return self._breakers.get(callback_id)

    def remove(self, callback_id: str):
        """移除熔断器。"""
        with self._lock:
            self._breakers.pop(callback_id, None)

    def all_states(self) -> dict[str, str]:
        """返回所有熔断器的状态快照。"""
        with self._lock:
            return {
                name: breaker.state.name
                for name, breaker in self._breakers.items()
            }
