"""
回调注册表 —— EventType → list[Callback] 映射

张小龙负责。核心数据结构，所有投递操作的起点。
线程安全：依赖 threading.Lock 保护所有写操作和快照读取。
"""

import threading
import uuid
from typing import Callable, Optional


# ── 类型别名 ──────────────────────────────────────────────────────────────

# EventType 就是字符串：事件主题（topic），如 "feifei:task_complete"
EventType = str

# Callback 是一个可调用对象，接收 (event_id, topic, payload, metadata_dict)
# 返回 True=成功, False=失败（触发重试/熔断器）
Callback = Callable[[str, str, dict, dict], bool]


# ── 异常 ──────────────────────────────────────────────────────────────────

class RegistryError(Exception):
    """注册表操作异常基类"""


class CallbackNotFoundError(RegistryError):
    """回调未找到"""


class DuplicateCallbackError(RegistryError):
    """重复注册（相同的 callback_id）"""


# ── 回调注册表 ────────────────────────────────────────────────────────────

class CallbackRegistry:
    """
    线程安全的回调注册表。

    数据结构:
        self._callbacks: dict[EventType, list[CallbackEntry]]
        其中 CallbackEntry = (callback_id, callback_fn, metadata_dict)

    设计要点:
        - register_callback 返回唯一 callback_id (uuid4 hex)
        - unregister_callback 通过 callback_id 删除，而非函数引用
        - list_callbacks 返回拷贝，避免外部篡改
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._callbacks: dict[EventType, list[dict]] = {}
        # ^ 每个 entry: {"id": str, "fn": Callback, "meta": dict}

    # ── 注册 ──────────────────────────────────────────────────────────────

    def register_callback(
        self,
        event_type: EventType,
        callback: Callback,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        注册一个回调。

        参数:
            event_type: 事件主题（支持通配符如 "feifei:*"）
            callback: 可调用对象，fn(event_id, topic, payload, metadata) -> bool
            metadata: 附加元数据（可选）

        返回:
            callback_id: 唯一标识，用于后续注销

        抛出:
            TypeError: callback 不可调用
        """
        if not callable(callback):
            raise TypeError(f"callback 必须可调用，收到 {type(callback)}")

        callback_id = uuid.uuid4().hex
        entry = {
            "id": callback_id,
            "fn": callback,
            "meta": metadata if metadata is not None else {},
        }

        with self._lock:
            if event_type not in self._callbacks:
                self._callbacks[event_type] = []
            # 检查重复 id（理论上 uuid4 不会冲突，但防御性检查）
            for existing in self._callbacks[event_type]:
                if existing["id"] == callback_id:
                    raise DuplicateCallbackError(
                        f"callback_id {callback_id} 已存在（极低概率 uuid 冲突）"
                    )
            self._callbacks[event_type].append(entry)

        return callback_id

    # ── 注销 ──────────────────────────────────────────────────────────────

    def unregister_callback(self, callback_id: str) -> bool:
        """
        通过 callback_id 注销回调。

        返回:
            True=找到并删除, False=未找到
        """
        with self._lock:
            for event_type in list(self._callbacks.keys()):
                before = len(self._callbacks[event_type])
                self._callbacks[event_type] = [
                    entry for entry in self._callbacks[event_type]
                    if entry["id"] != callback_id
                ]
                after = len(self._callbacks[event_type])
                if after < before:
                    # 清理空列表
                    if after == 0:
                        del self._callbacks[event_type]
                    return True
        return False

    # ── 列表 ──────────────────────────────────────────────────────────────

    def list_callbacks(
        self,
        event_type: Optional[EventType] = None,
    ) -> list[dict]:
        """
        列出已注册的回调。

        参数:
            event_type: 如果指定，只返回该主题的回调；否则返回全部

        返回:
            list[{"id", "event_type", "meta"}]  （不包含 fn 引用本身）
        """
        with self._lock:
            if event_type is not None:
                entries = self._callbacks.get(event_type, [])
                return [
                    {"id": e["id"], "event_type": event_type, "meta": e["meta"]}
                    for e in entries
                ]
            else:
                result = []
                for et, entries in self._callbacks.items():
                    for e in entries:
                        result.append({
                            "id": e["id"],
                            "event_type": et,
                            "meta": e["meta"],
                        })
                return result

    # ── 查询 ──────────────────────────────────────────────────────────────

    def get_callbacks_for_event(
        self,
        event_type: EventType,
        topic: str,
    ) -> list[dict]:
        """
        获取与指定事件主题匹配的所有回调（含通配符匹配）。

        匹配规则:
            - "feifei:task_complete" 精确匹配
            - "feifei:*" 通配匹配 "feifei:xxx"
            - "*" 匹配所有

        返回:
            list[{"id", "fn", "meta"}]  包含可调用的 fn
        """
        with self._lock:
            matched = []

            # 1. 精确匹配
            if event_type in self._callbacks:
                matched.extend(self._callbacks[event_type])

            # 2. 通配匹配
            for et, entries in self._callbacks.items():
                if et == event_type:
                    continue  # 已在上面处理
                if et == "*":
                    matched.extend(entries)
                elif et.endswith(":*"):
                    prefix = et[:-2]  # 去掉 ":*"
                    if topic.startswith(prefix):
                        matched.extend(entries)
                elif et.startswith("*:"):
                    suffix = et[2:]  # 去掉 "*:"
                    if topic.endswith(suffix):
                        matched.extend(entries)

            return matched

    # ── 快照（用于持久化） ──────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """
        返回注册表的可序列化快照。

        注意: callback 函数不可序列化，快照仅包含 id 和 meta。
        函数本身在恢复时需要重新注册。
        """
        with self._lock:
            result = {}
            for et, entries in self._callbacks.items():
                result[et] = [
                    {"id": e["id"], "meta": e["meta"]}
                    for e in entries
                ]
            return result

    def size(self) -> int:
        """返回注册回调总数。"""
        with self._lock:
            return sum(len(entries) for entries in self._callbacks.values())
