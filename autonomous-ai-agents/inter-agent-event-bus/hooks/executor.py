"""
投递执行器 —— 并行 fork 所有回调，各自隔离超时/重试/熔断器

核心逻辑:
    1. 收到事件，查询注册表获取匹配回调
    2. 对每个回调，创建独立线程执行
    3. 每个线程内部：
       a. 检查熔断器 guard() → 熔断则跳过
       b. 执行 RetryPolicy.execute() 包裹回调
       c. 成功 → 熔断器 on_success()
       d. 失败 → 熔断器 on_failure()
       e. 重试耗尽 → 写入 DLQ
    4. 主线程等待所有子线程（带总超时）

张小龙设计。纯 Python stdlib。
"""

import threading
import time
import logging
from typing import Callable, Optional

from .registry import CallbackRegistry, EventType
from .breaker import BreakerRegistry, CircuitBreaker, BreakerEvent, BreakerState
from .retry import RetryPolicy, RetryResult
from .dlq import DeadLetterQueue, DeadLetterEntry

logger = logging.getLogger(__name__)


# ── 投递结果 ──────────────────────────────────────────────────────────────

class DeliveryResult:
    """
    单次事件投递的最终结果。

    字段:
        event_id: 事件 ID
        topic: 事件主题
        callback_id: 回调 ID
        success: 是否成功
        breaker_state: 执行时的熔断器状态
        retry_result: 重试结果（如有）
        dlq_written: 是否已写入死信
        error: 错误描述（如有）
        duration: 总耗时（秒）
    """

    __slots__ = (
        "event_id", "topic", "callback_id", "success",
        "breaker_state", "retry_result", "dlq_written",
        "error", "duration",
    )

    def __init__(
        self,
        event_id: str,
        topic: str,
        callback_id: str,
        success: bool = False,
        breaker_state: Optional[str] = None,
        retry_result: Optional[RetryResult] = None,
        dlq_written: bool = False,
        error: Optional[str] = None,
        duration: float = 0.0,
    ):
        self.event_id = event_id
        self.topic = topic
        self.callback_id = callback_id
        self.success = success
        self.breaker_state = breaker_state
        self.retry_result = retry_result
        self.dlq_written = dlq_written
        self.error = error
        self.duration = duration

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return (
            f"DeliveryResult({status} cb={self.callback_id[:8]}... "
            f"event={self.event_id[:8]}... "
            f"duration={self.duration:.3f}s)"
        )


# ── 投递执行器 ────────────────────────────────────────────────────────────

class DeliveryExecutor:
    """
    投递执行器。
    将事件投递给所有匹配的回调，每个回调在独立线程中执行。

    参数:
        registry: CallbackRegistry 实例
        breaker_registry: BreakerRegistry 实例（可选，默认新建）
        dlq: DeadLetterQueue 实例（可选，默认不启用死信）
        default_retry_policy: 默认重试策略（可选，默认 RetryPolicy()）
        global_timeout: 所有回调的总超时（秒，默认 60.0）
        breaker_listener: 熔断器状态变更监听器（可选）
    """

    def __init__(
        self,
        registry: CallbackRegistry,
        breaker_registry: Optional[BreakerRegistry] = None,
        dlq: Optional[DeadLetterQueue] = None,
        default_retry_policy: Optional[RetryPolicy] = None,
        global_timeout: float = 60.0,
        breaker_listener: Optional[Callable[[BreakerEvent], None]] = None,
    ):
        self._registry = registry
        self._breaker_registry = breaker_registry or BreakerRegistry()
        self._dlq = dlq
        self._default_retry_policy = default_retry_policy or RetryPolicy()
        self._global_timeout = global_timeout
        self._breaker_listener = breaker_listener

    # ── 公共接口 ──────────────────────────────────────────────────────────

    def deliver(
        self,
        event_id: str,
        topic: str,
        payload: dict,
        metadata: Optional[dict] = None,
    ) -> list[DeliveryResult]:
        """
        投递事件给所有匹配的回调。

        参数:
            event_id: 事件唯一 ID
            topic: 事件主题
            payload: 事件负载
            metadata: 附加元数据（可选），会传递给回调

        返回:
            list[DeliveryResult] 每个回调一个结果
        """
        metadata = metadata or {}
        start_time = time.time()

        # 查询匹配的回调
        callbacks = self._registry.get_callbacks_for_event(topic, topic)
        if not callbacks:
            logger.debug("事件 [%s] 主题 [%s] 无匹配回调", event_id[:8], topic)
            return []

        logger.info(
            "投递事件 [%s] topic=%s 匹配到 %d 个回调",
            event_id[:8], topic, len(callbacks),
        )

        # 为每个回调创建执行线程
        threads: list[threading.Thread] = []
        results: list[DeliveryResult] = []
        results_lock = threading.Lock()

        for cb_entry in callbacks:
            cb_id = cb_entry["id"]
            cb_fn = cb_entry["fn"]
            cb_meta = cb_entry.get("meta", {})

            thread = threading.Thread(
                target=self._execute_single_callback,
                args=(
                    event_id, topic, payload, metadata,
                    cb_id, cb_fn, cb_meta,
                    results, results_lock, start_time,
                ),
                daemon=True,
            )
            threads.append(thread)
            thread.start()

        # 等待所有线程完成（或超时）
        for thread in threads:
            thread.join(timeout=self._global_timeout)

        # 检查是否有线程超时
        for i, thread in enumerate(threads):
            if thread.is_alive():
                logger.warning(
                    "回调线程超时 [%s]", callbacks[i]["id"][:8]
                )

        logger.info(
            "投递完成 [%s] topic=%s 成功=%d/%d",
            event_id[:8], topic,
            sum(1 for r in results if r.success),
            len(results),
        )

        return results

    # ── 单回调执行 ────────────────────────────────────────────────────────

    def _execute_single_callback(
        self,
        event_id: str,
        topic: str,
        payload: dict,
        metadata: dict,
        cb_id: str,
        cb_fn: Callable,
        cb_meta: dict,
        results: list,
        results_lock: threading.Lock,
        start_time: float,
    ):
        """
        在独立线程中执行单个回调。

        流程:
            1. 熔断器 guard
            2. RetryPolicy 包裹回调
            3. 成功/失败 回报熔断器
            4. 重试耗尽 → DLQ
        """
        t0 = time.time()
        try:
            # 1. 熔断器检查
            breaker = self._breaker_registry.get_or_create(
                callback_id=cb_id,
                listener=self._breaker_listener,
            )

            if not breaker.guard():
                elapsed = time.time() - t0
                result = DeliveryResult(
                    event_id=event_id,
                    topic=topic,
                    callback_id=cb_id,
                    success=False,
                    breaker_state=breaker.state.name,
                    error=f"熔断器拒绝: state={breaker.state.name}",
                    duration=elapsed,
                )
                logger.warning(
                    "熔断器拒绝回调 [%s] event=%s state=%s",
                    cb_id[:8], event_id[:8], breaker.state.name,
                )
                with results_lock:
                    results.append(result)
                return

            # 2. 构建回调函数（闭包，捕获参数）
            def run_callback() -> bool:
                """单次调用封装。"""
                # 合并 metadata 和 cb_meta
                call_meta = dict(metadata)
                call_meta["callback_meta"] = cb_meta
                return cb_fn(event_id, topic, payload, call_meta)

            # 3. 执行重试策略
            retry_policy = RetryPolicy(
                max_retries=cb_meta.get("max_retries", 3),
                base_delay=cb_meta.get("base_delay", 1.0),
                max_delay=cb_meta.get("max_delay", 30.0),
            )
            retry_result = retry_policy.execute(
                run_callback,
                context_info=f"cb={cb_id[:8]}, event={event_id[:8]}",
            )

            # 4. 回报熔断器
            if retry_result.success:
                breaker.on_success()
            else:
                breaker.on_failure()

            # 5. 重试耗尽 → DLQ
            dlq_written = False
            if not retry_result.success and self._dlq is not None:
                dlq_entry = DeadLetterEntry(
                    event_id=event_id,
                    topic=topic,
                    payload=payload,
                    callback_id=cb_id,
                    callback_meta=cb_meta,
                    failure_reason=str(retry_result.last_error)
                        if retry_result.last_error
                        else "回调返回失败",
                    attempts=retry_result.attempts,
                    total_time_ms=retry_result.total_time * 1000,
                )
                self._dlq.write(dlq_entry)
                dlq_written = True

            elapsed = time.time() - t0
            result = DeliveryResult(
                event_id=event_id,
                topic=topic,
                callback_id=cb_id,
                success=retry_result.success,
                breaker_state=breaker.state.name,
                retry_result=retry_result,
                dlq_written=dlq_written,
                duration=elapsed,
            )

            with results_lock:
                results.append(result)

        except Exception as exc:
            elapsed = time.time() - t0
            logger.exception(
                "回调执行异常 [%s] event=%s: %s",
                cb_id[:8], event_id[:8], exc,
            )
            result = DeliveryResult(
                event_id=event_id,
                topic=topic,
                callback_id=cb_id,
                success=False,
                error=f"未捕获异常: {type(exc).__name__}: {exc}",
                duration=elapsed,
            )
            with results_lock:
                results.append(result)


# ── 便捷工厂 ──────────────────────────────────────────────────────────────

def create_delivery_executor(
    db_path: Optional[str] = None,
    breaker_listener: Optional[Callable[[BreakerEvent], None]] = None,
) -> DeliveryExecutor:
    """
    创建配置好的投递执行器。

    参数:
        db_path: SQLite 数据库路径（用于 DLQ），None 则不启用 DLQ
        breaker_listener: 熔断器状态变更监听器
    """
    registry = CallbackRegistry()
    breaker_registry = BreakerRegistry()
    dlq = DeadLetterQueue(db_path) if db_path else None

    return DeliveryExecutor(
        registry=registry,
        breaker_registry=breaker_registry,
        dlq=dlq,
        breaker_listener=breaker_listener,
    )
