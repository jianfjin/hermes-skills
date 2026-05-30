# delivery hooks —— 回调注册、熔断、重试、死信、持久化
# 张小龙 (Zhang Xiaolong) — 29年工程经验
# Foxmail → QQ Mail → WeChat → Hermes

from .registry import CallbackRegistry, EventType, Callback
from .breaker import CircuitBreaker, BreakerState, BreakerEvent
from .retry import RetryPolicy, RetryResult
from .executor import DeliveryExecutor
from .dlq import DeadLetterQueue, DeadLetterEntry
from .persistence import SnapshotManager
from .hooks import setup_delivery_hooks, get_registry

__all__ = [
    "CallbackRegistry", "EventType", "Callback",
    "CircuitBreaker", "BreakerState", "BreakerEvent",
    "RetryPolicy", "RetryResult",
    "DeliveryExecutor",
    "DeadLetterQueue", "DeadLetterEntry",
    "SnapshotManager",
    "setup_delivery_hooks",
    "get_registry",
]
