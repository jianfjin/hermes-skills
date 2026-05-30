"""
重试策略 —— 指数退避 + jitter

策略:
    - 指数退避: 1s, 2s, 4s, 8s ...  capped 30s
    - 抖动: ±25% 随机偏移
    - 默认最大重试次数: 3
    - 总超时: 无硬限制（由调用方控制）

张小龙设计。纯 Python stdlib。
"""

import random
import time
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


# ── 重试结果 ──────────────────────────────────────────────────────────────

class RetryResult:
    """
    重试执行最终结果。

    字段:
        success: bool — 是否最终成功
        attempts: int — 总尝试次数（含首次）
        last_error: Optional[Exception] — 最后一次异常
        total_time: float — 总耗时（秒）
        attempt_times: list[float] — 每次耗时
    """

    __slots__ = (
        "success", "attempts", "last_error",
        "total_time", "attempt_times",
    )

    def __init__(
        self,
        success: bool,
        attempts: int,
        last_error: Optional[Exception] = None,
        total_time: float = 0.0,
        attempt_times: Optional[list[float]] = None,
    ):
        self.success = success
        self.attempts = attempts
        self.last_error = last_error
        self.total_time = total_time
        self.attempt_times = attempt_times or []

    def __repr__(self):
        status = "✓" if self.success else "✗"
        return (
            f"RetryResult({status} attempts={self.attempts}, "
            f"total_time={self.total_time:.3f}s, "
            f"error={self.last_error})"
        )


# ── 重试策略 ──────────────────────────────────────────────────────────────

class RetryPolicy:
    """
    可配置的重试策略。

    参数:
        max_retries: 最大重试次数（不含首次调用）（默认 3）
        base_delay: 初始退避秒数（默认 1.0）
        max_delay: 最大退避秒数，capped（默认 30.0）
        jitter_ratio: 抖动幅度，±百分比（默认 0.25 = ±25%）
        retryable_exceptions: 可重试的异常类型元组（默认 (Exception,)）
    """

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        jitter_ratio: float = 0.25,
        retryable_exceptions: tuple = (Exception,),
    ):
        if max_retries < 0:
            raise ValueError("max_retries 不能为负")
        if base_delay <= 0:
            raise ValueError("base_delay 必须 > 0")
        if max_delay < base_delay:
            raise ValueError("max_delay 不能小于 base_delay")
        if not (0 <= jitter_ratio <= 1):
            raise ValueError("jitter_ratio 必须在 [0, 1] 之间")

        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter_ratio = jitter_ratio
        self.retryable_exceptions = retryable_exceptions

    def get_delay(self, attempt: int) -> float:
        """
        计算第 attempt 次重试前的等待时间（1-indexed）。

        公式:
            delay = min(base_delay * 2^(attempt-1), max_delay)
            jitter = delay * random.uniform(-jitter_ratio, +jitter_ratio)
            final = delay + jitter

        确保 final >= 0。
        """
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        jitter = delay * random.uniform(-self.jitter_ratio, self.jitter_ratio)
        return max(0.0, delay + jitter)

    def execute(
        self,
        fn: Callable[[], bool],
        context_info: Optional[str] = None,
    ) -> RetryResult:
        """
        带重试策略执行函数。

        参数:
            fn: 无参可调用，返回 bool（True=成功, False=失败）
            context_info: 日志上下文信息

        返回:
            RetryResult
        """
        tag = context_info or ""

        attempts = 0
        last_error: Optional[Exception] = None
        start_time = time.time()
        attempt_times: list[float] = []

        while attempts <= self.max_retries:
            attempts += 1
            t0 = time.time()

            try:
                result = fn()
                elapsed = time.time() - t0
                attempt_times.append(elapsed)

                if result:
                    total_time = time.time() - start_time
                    logger.debug(
                        "重试执行成功 [%s] attempt=%d/%d elapsed=%.3fs",
                        tag, attempts, self.max_retries + 1, elapsed
                    )
                    return RetryResult(
                        success=True,
                        attempts=attempts,
                        total_time=total_time,
                        attempt_times=attempt_times,
                    )
                else:
                    last_error = None  # 函数返回 False 不是异常
                    elapsed = time.time() - t0
                    attempt_times.append(elapsed)
                    logger.warning(
                        "重试返回失败 [%s] attempt=%d/%d elapsed=%.3fs",
                        tag, attempts, self.max_retries + 1, elapsed
                    )

            except self.retryable_exceptions as exc:
                elapsed = time.time() - t0
                attempt_times.append(elapsed)
                last_error = exc
                logger.warning(
                    "重试异常 [%s] attempt=%d/%d: %s: %s",
                    tag, attempts, self.max_retries + 1,
                    type(exc).__name__, exc,
                )

            # 如果需要等待（不是最后一次尝试）
            if attempts <= self.max_retries:
                delay = self.get_delay(attempts)
                logger.debug(
                    "重试等待 [%s] attempt=%d → %d, delay=%.3fs",
                    tag, attempts, attempts + 1, delay
                )
                time.sleep(delay)

        total_time = time.time() - start_time
        logger.error(
            "重试耗尽 [%s] attempts=%d total_time=%.3fs last_error=%s",
            tag, attempts, total_time, last_error
        )
        return RetryResult(
            success=False,
            attempts=attempts,
            last_error=last_error,
            total_time=total_time,
            attempt_times=attempt_times,
        )
