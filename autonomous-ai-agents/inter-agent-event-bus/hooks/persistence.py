"""
持久化快照 —— 事件触发 + 每 5 分钟自动保存回调注册表

两种触发方式:
    1. 事件触发: 每次 register/unregister 后自动保存
    2. 定时保存: 后台线程每 5 分钟保存一次

快照格式: JSON 文件，仅保存回调的 id 和 meta（函数不可序列化）。
恢复时需要调用方重新注册 callback 函数。

存储路径: ~/.hermes/hermes-agent/skills/autonomous-ai-agents/inter-agent-event-bus/hooks/snapshot.json

张小龙设计。纯 Python stdlib。
"""

import json
import os
import threading
import time
import logging
from typing import Optional

from .registry import CallbackRegistry

logger = logging.getLogger(__name__)

# 默认快照文件路径
DEFAULT_SNAPSHOT_PATH = os.path.join(
    os.path.expanduser("~"),
    ".hermes",
    "hermes-agent",
    "skills",
    "autonomous-ai-agents",
    "inter-agent-event-bus",
    "hooks",
    "snapshot.json",
)

# 自动保存间隔（秒）
DEFAULT_AUTO_SAVE_INTERVAL = 300  # 5 分钟


# ── 快照管理器 ────────────────────────────────────────────────────────────

class SnapshotManager:
    """
    回调注册表快照管理器。

    职责:
        - save(): 将注册表快照写入 JSON 文件
        - load(): 从 JSON 文件恢复注册表快照（不含回调函数）
        - start_auto_save(): 启动后台自动保存线程
        - stop_auto_save(): 停止后台自动保存线程

    用法:
        registry = CallbackRegistry()
        snap = SnapshotManager(registry)
        snap.start_auto_save()
        # ... 注册回调 ...
        snap.save()  # 手动保存
        snap.stop_auto_save()
    """

    def __init__(
        self,
        registry: CallbackRegistry,
        file_path: str = DEFAULT_SNAPSHOT_PATH,
        auto_save_interval: float = DEFAULT_AUTO_SAVE_INTERVAL,
    ):
        self._registry = registry
        self._file_path = file_path
        self._auto_save_interval = auto_save_interval

        self._auto_save_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    # ── 保存 ──────────────────────────────────────────────────────────────

    def save(self) -> str:
        """
        将注册表快照写入 JSON 文件。

        返回:
            写入的文件路径

        文件格式:
            {
                "version": 1,
                "saved_at": 1234567890.123,
                "callbacks": {
                    "feifei:task_complete": [
                        {"id": "abc...", "meta": {...}},
                        ...
                    ],
                    ...
                }
            }
        """
        with self._lock:
            snapshot_data = self._registry.snapshot()
            payload = {
                "version": 1,
                "saved_at": time.time(),
                "callbacks": snapshot_data,
            }

            # 确保目录存在
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)

            # 原子写入：先写临时文件，再 rename
            tmp_path = self._file_path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            os.replace(tmp_path, self._file_path)

            count = sum(len(v) for v in snapshot_data.values())
            logger.info(
                "快照已保存 [%s] %d 个回调, 文件=%s",
                time.strftime("%H:%M:%S"), count, self._file_path,
            )

        return self._file_path

    # ── 加载 ──────────────────────────────────────────────────────────────

    def load(self) -> Optional[dict]:
        """
        从 JSON 文件加载快照。

        返回:
            dict: {"callbacks": {event_type: [{"id": ..., "meta": ...}, ...]}}
            或 None（文件不存在或损坏）
        """
        if not os.path.exists(self._file_path):
            logger.info("快照文件不存在: %s", self._file_path)
            return None

        try:
            # 注意：这个load不是在__init__中调用的，所以不需要锁
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            callbacks = data.get("callbacks", {})
            count = sum(len(v) for v in callbacks.values())

            logger.info(
                "快照已加载 [%s] %d 个回调, 文件=%s",
                time.strftime("%H:%M:%S"), count, self._file_path,
            )
            return data

        except (json.JSONDecodeError, OSError) as exc:
            logger.error("快照加载失败: %s", exc)
            return None

    # ── 自动保存 ──────────────────────────────────────────────────────────

    def start_auto_save(self):
        """
        启动后台自动保存线程。
        每 auto_save_interval 秒保存一次。
        线程为 daemon，不会阻止进程退出。
        """
        if self._auto_save_thread is not None and self._auto_save_thread.is_alive():
            logger.warning("自动保存线程已在运行")
            return

        self._stop_event.clear()
        self._auto_save_thread = threading.Thread(
            target=self._auto_save_loop,
            daemon=True,
            name="snapshot-auto-save",
        )
        self._auto_save_thread.start()
        logger.info(
            "自动保存已启动 (interval=%ds)", self._auto_save_interval
        )

    def stop_auto_save(self):
        """停止后台自动保存线程。"""
        if self._auto_save_thread is None:
            return

        self._stop_event.set()
        self._auto_save_thread.join(timeout=10.0)
        if self._auto_save_thread.is_alive():
            logger.warning("自动保存线程未能在 10s 内停止")
        else:
            logger.info("自动保存已停止")
        self._auto_save_thread = None

    def _auto_save_loop(self):
        """自动保存循环（后台线程运行）。"""
        while not self._stop_event.is_set():
            # 等待 interval 或收到停止信号
            if self._stop_event.wait(self._auto_save_interval):
                break
            try:
                self.save()
            except Exception as exc:
                logger.error("自动保存失败: %s", exc)

    # ── 便利方法 ──────────────────────────────────────────────────────────

    @property
    def file_path(self) -> str:
        return self._file_path

    def last_saved_timestamp(self) -> Optional[float]:
        """返回最后一次保存的时间戳，或 None。"""
        try:
            if os.path.exists(self._file_path):
                return os.path.getmtime(self._file_path)
        except OSError:
            pass
        return None
