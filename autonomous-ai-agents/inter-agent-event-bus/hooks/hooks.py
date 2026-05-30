"""
Delivery Hooks —— 事件总线投递钩子的集成入口

作为 inter-agent-event-bus skill 的 delivery hooks 插件。
当事件被 publish 后，hooks.py 自动将事件投递给所有注册的回调。

张小龙 (Zhang Xiaolong) — 29年工程经验
Foxmail → QQ Mail → WeChat → Hermes

挂钩点:
    - deliver_event(event_id, topic, payload) → list[DeliveryResult]
      publish_event 在写入 events 表后调用此函数
    - 回调注册/注销 → 自动触发快照保存
    - 熔断器状态变更 → 日志 + 可选外部通知

用法:
    from hooks import setup_delivery_hooks

    hooks = setup_delivery_hooks(
        db_path="/path/to/event_bus.db",
        snapshot_path="/path/to/snapshot.json",
    )

    # 注册回调
    def on_task_complete(event_id, topic, payload, meta):
        print(f"收到: {payload}")
        return True

    cb_id = hooks.register_callback("feifei:task_complete", on_task_complete)

    # 投递事件（由 publish_event 调用）
    results = hooks.deliver_event(
        event_id="abc123",
        topic="feifei:task_complete",
        payload={"task_id": 42, "status": "done"},
    )

    # 查询
    hooks.list_callbacks()
    hooks.dead_letter_query()
    hooks.breaker_states()
"""

import logging
import threading
from typing import Callable, Optional

from .registry import CallbackRegistry, EventType, Callback
from .breaker import BreakerRegistry, BreakerEvent, BreakerState
from .executor import DeliveryExecutor, DeliveryResult
from .dlq import DeadLetterQueue, DeadLetterEntry
from .persistence import SnapshotManager, DEFAULT_SNAPSHOT_PATH

logger = logging.getLogger(__name__)


# ── Hook 管理器 ───────────────────────────────────────────────────────────

class DeliveryHooks:
    """
    Delivery Hooks 管理器 —— 集成了注册表、熔断器、执行器、DLQ、持久化。

    对外暴露一组简洁的 API，供事件总线和外部使用。
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        snapshot_path: str = DEFAULT_SNAPSHOT_PATH,
        auto_save_interval: float = 300.0,  # 5 分钟
    ):
        # 组件初始化
        self._registry = CallbackRegistry()
        self._breaker_registry = BreakerRegistry()
        self._dlq = DeadLetterQueue(db_path) if db_path else None
        self._snapshot = SnapshotManager(
            registry=self._registry,
            file_path=snapshot_path,
            auto_save_interval=auto_save_interval,
        )
        self._executor = DeliveryExecutor(
            registry=self._registry,
            breaker_registry=self._breaker_registry,
            dlq=self._dlq,
            breaker_listener=self._on_breaker_event,
        )

        # 恢复快照
        self._load_snapshot()

        # 启动自动保存
        self._snapshot.start_auto_save()

    # ── 回调注册管理 ──────────────────────────────────────────────────────

    def register_callback(
        self,
        event_type: EventType,
        callback: Callback,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        注册回调。

        注册后自动保存快照。
        """
        cb_id = self._registry.register_callback(event_type, callback, metadata)
        self._snapshot.save()  # 事件触发式保存
        logger.info(
            "回调已注册 [%s] event_type=%s",
            cb_id[:8], event_type,
        )
        return cb_id

    def unregister_callback(self, callback_id: str) -> bool:
        """
        注销回调。

        注销后自动保存快照，并清理熔断器。
        """
        removed = self._registry.unregister_callback(callback_id)
        if removed:
            self._breaker_registry.remove(callback_id)
            self._snapshot.save()  # 事件触发式保存
            logger.info("回调已注销 [%s]", callback_id[:8])
        else:
            logger.warning("回调注销失败（未找到）[%s]", callback_id[:8])
        return removed

    def list_callbacks(
        self,
        event_type: Optional[EventType] = None,
    ) -> list[dict]:
        """列出已注册的回调。"""
        return self._registry.list_callbacks(event_type)

    # ── 事件投递 ──────────────────────────────────────────────────────────

    def deliver_event(
        self,
        event_id: str,
        topic: str,
        payload: dict,
        metadata: Optional[dict] = None,
    ) -> list[DeliveryResult]:
        """
        投递事件给所有匹配的回调。

        由 publish_event 在写入 events 表后调用。
        """
        return self._executor.deliver(event_id, topic, payload, metadata)

    # ── 熔断器状态 ────────────────────────────────────────────────────────

    def breaker_states(self) -> dict[str, str]:
        """返回所有熔断器的状态。"""
        return self._breaker_registry.all_states()

    def reset_breaker(self, callback_id: str):
        """手动重置指定熔断器。"""
        breaker = self._breaker_registry.get(callback_id)
        if breaker:
            breaker.reset()
            return True
        return False

    # ── 死信查询 ──────────────────────────────────────────────────────────

    def dead_letter_query(
        self,
        limit: int = 50,
        offset: int = 0,
        topic: Optional[str] = None,
    ) -> list[DeadLetterEntry]:
        """查询死信记录。"""
        if self._dlq:
            return self._dlq.query(limit=limit, offset=offset, topic=topic)
        return []

    def dead_letter_count(self, topic: Optional[str] = None) -> int:
        """返回死信记录数。"""
        if self._dlq:
            return self._dlq.count(topic=topic)
        return 0

    def dead_letter_purge(self, before_timestamp: float) -> int:
        """清理死信记录。"""
        if self._dlq:
            return self._dlq.purge(before_timestamp)
        return 0

    # ── 快照 ──────────────────────────────────────────────────────────────

    def save_snapshot(self):
        """手动保存快照。"""
        return self._snapshot.save()

    # ── 资源清理 ──────────────────────────────────────────────────────────

    def shutdown(self):
        """关闭所有后台线程，释放资源。"""
        self._snapshot.stop_auto_save()
        logger.info("DeliveryHooks 已关闭")

    # ── 内部 ──────────────────────────────────────────────────────────────

    def _on_breaker_event(self, event: BreakerEvent):
        """
        熔断器状态变更的默认监听器。

        可在 setup_delivery_hooks 中通过 breaker_listener 覆盖。
        """
        level = (
            logging.WARNING
            if event.new_state in (BreakerState.OPEN,)
            else logging.INFO
        )
        logger.log(
            level,
            "熔断器事件 [%s] %s → %s | 原因: %s | 失败计数: %d",
            event.breaker_name[:8],
            event.old_state.name,
            event.new_state.name,
            event.reason,
            event.failure_count,
        )

    def _load_snapshot(self):
        """从快照恢复回调注册信息（仅 meta，函数需重新注册）。"""
        data = self._snapshot.load()
        if data is None:
            return

        callbacks = data.get("callbacks", {})
        loaded_count = 0
        for event_type, entries in callbacks.items():
            for entry in entries:
                # 快照中仅保存 id 和 meta，函数需要外部重新注册
                # 此处只记录日志，不自动注册（函数不可反序列化）
                loaded_count += 1
                logger.debug(
                    "快照回调 [%s] event_type=%s meta=%s （需外部注册函数）",
                    entry["id"][:8], event_type, entry.get("meta"),
                )

        logger.info(
            "快照加载完成: 共 %d 个回调记录（函数需外部重新注册）",
            loaded_count,
        )


# ── 全局单例（供 publish_event 延迟发现） ──────────────────────────────────

_global_hooks: Optional['DeliveryHooks'] = None
_global_hooks_lock = threading.Lock()


# ── 工厂函数 ──────────────────────────────────────────────────────────────

def setup_delivery_hooks(
    db_path: Optional[str] = None,
    snapshot_path: str = DEFAULT_SNAPSHOT_PATH,
    auto_save_interval: float = 300.0,
) -> DeliveryHooks:
    """
    创建并初始化 DeliveryHooks 实例，注册为全局单例。

    这是推荐的入口函数。多次调用会返回同一个实例。

    参数:
        db_path: SQLite 数据库路径（用于 DLQ），None 则不启用死信
        snapshot_path: 快照文件路径
        auto_save_interval: 自动保存间隔（秒），默认 300 (5分钟)

    返回:
        DeliveryHooks 实例

    用法:
        hooks = setup_delivery_hooks(
            db_path="/path/to/event_bus.db",
        )
        hooks.register_callback("feifei:*", my_callback)
        hooks.deliver_event("evt_001", "feifei:done", {"ok": True})
    """
    global _global_hooks
    with _global_hooks_lock:
        if _global_hooks is not None:
            return _global_hooks
        _global_hooks = DeliveryHooks(
            db_path=db_path,
            snapshot_path=snapshot_path,
            auto_save_interval=auto_save_interval,
        )
        return _global_hooks


def get_registry() -> Optional[DeliveryHooks]:
    """
    获取全局 DeliveryHooks 单例（线程安全）。

    未调用 setup_delivery_hooks() 前返回 None。
    publish_event 通过此函数延迟发现 hooks 是否已初始化。
    """
    global _global_hooks
    return _global_hooks
