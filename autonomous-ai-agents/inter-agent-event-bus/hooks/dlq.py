"""
死信队列 (Dead Letter Queue) —— 重试耗尽事件的归宿

当回调重试次数耗尽后，事件被写入死信表，供人工或自动系统后续分析。
DLQ 存储在 SQLite 数据库中（与事件总线共享同一 SQLite 连接）。

表结构:
    CREATE TABLE IF NOT EXISTS dead_letter_queue (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id        TEXT NOT NULL,
        topic           TEXT NOT NULL,
        payload         TEXT NOT NULL,       -- JSON 序列化
        callback_id     TEXT NOT NULL,
        callback_meta   TEXT DEFAULT '{}',   -- JSON
        failure_reason  TEXT,                -- 最终失败原因
        attempts        INTEGER NOT NULL,
        total_time_ms   REAL,
        created_at      REAL NOT NULL DEFAULT (julianday('now'))
    );

张小龙设计。纯 Python stdlib。
"""

import json
import sqlite3
import threading
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── 死信条目 ──────────────────────────────────────────────────────────────

class DeadLetterEntry:
    """
    死信条目数据类。

    字段:
        event_id: 原始事件 ID
        topic: 事件主题
        payload: 事件负载（dict）
        callback_id: 回调 ID
        callback_meta: 回调元数据（dict）
        failure_reason: 最终失败原因描述
        attempts: 总尝试次数
        total_time_ms: 总耗时（毫秒）
        created_at: 写入时间戳
    """

    __slots__ = (
        "event_id", "topic", "payload", "callback_id",
        "callback_meta", "failure_reason", "attempts",
        "total_time_ms", "created_at",
    )

    def __init__(
        self,
        event_id: str,
        topic: str,
        payload: dict,
        callback_id: str,
        callback_meta: Optional[dict] = None,
        failure_reason: Optional[str] = None,
        attempts: int = 0,
        total_time_ms: float = 0.0,
        created_at: Optional[float] = None,
    ):
        self.event_id = event_id
        self.topic = topic
        self.payload = payload
        self.callback_id = callback_id
        self.callback_meta = callback_meta or {}
        self.failure_reason = failure_reason
        self.attempts = attempts
        self.total_time_ms = total_time_ms
        self.created_at = created_at if created_at is not None else time.time()

    def __repr__(self):
        return (
            f"DeadLetterEntry(event_id={self.event_id!r}, "
            f"topic={self.topic!r}, "
            f"callback_id={self.callback_id!r}, "
            f"attempts={self.attempts})"
        )

    def to_dict(self) -> dict:
        """转 dict 用于序列化。"""
        return {
            "event_id": self.event_id,
            "topic": self.topic,
            "payload": self.payload,
            "callback_id": self.callback_id,
            "callback_meta": self.callback_meta,
            "failure_reason": self.failure_reason,
            "attempts": self.attempts,
            "total_time_ms": self.total_time_ms,
            "created_at": self.created_at,
        }


# ── 死信队列 ──────────────────────────────────────────────────────────────

class DeadLetterQueue:
    """
    死信队列管理器。

    参数:
        db_path: SQLite 数据库路径
        auto_init: 是否自动初始化表结构（默认 True）

    线程安全: 使用 threading.Lock 保护写入。
    """

    def __init__(self, db_path: str, auto_init: bool = True):
        self._db_path = db_path
        self._lock = threading.Lock()
        self._conn: Optional[sqlite3.Connection] = None

        if auto_init:
            self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """惰性初始化数据库连接。"""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self._db_path,
                check_same_thread=False,
            )
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
        return self._conn

    def _init_db(self):
        """创建死信表（如不存在）。"""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dead_letter_queue (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id        TEXT NOT NULL,
                topic           TEXT NOT NULL,
                payload         TEXT NOT NULL,
                callback_id     TEXT NOT NULL,
                callback_meta   TEXT DEFAULT '{}',
                failure_reason  TEXT,
                attempts        INTEGER NOT NULL,
                total_time_ms   REAL,
                created_at      REAL NOT NULL DEFAULT (julianday('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dlq_event_id
            ON dead_letter_queue(event_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_dlq_created
            ON dead_letter_queue(created_at)
        """)
        conn.commit()

    # ── 写入 ──────────────────────────────────────────────────────────────

    def write(
        self,
        entry: DeadLetterEntry,
    ) -> int:
        """
        写入一条死信记录。

        返回:
            插入行的 id
        """
        conn = self._get_conn()
        payload_json = json.dumps(entry.payload, ensure_ascii=False)
        meta_json = json.dumps(entry.callback_meta, ensure_ascii=False)

        with self._lock:
            cursor = conn.execute(
                """
                INSERT INTO dead_letter_queue
                    (event_id, topic, payload, callback_id,
                     callback_meta, failure_reason, attempts,
                     total_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.event_id,
                    entry.topic,
                    payload_json,
                    entry.callback_id,
                    meta_json,
                    entry.failure_reason,
                    entry.attempts,
                    entry.total_time_ms,
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid

        logger.info(
            "死信写入 [id=%d] event=%s topic=%s callback=%s attempts=%d",
            row_id, entry.event_id, entry.topic,
            entry.callback_id, entry.attempts,
        )
        return row_id

    # ── 查询 ──────────────────────────────────────────────────────────────

    def query(
        self,
        limit: int = 50,
        offset: int = 0,
        topic: Optional[str] = None,
    ) -> list[DeadLetterEntry]:
        """
        查询死信记录，按创建时间降序。

        参数:
            limit: 返回条数上限
            offset: 分页偏移
            topic: 按主题过滤（可选）
        """
        conn = self._get_conn()

        if topic:
            rows = conn.execute(
                """
                SELECT event_id, topic, payload, callback_id,
                       callback_meta, failure_reason, attempts,
                       total_time_ms, created_at
                FROM dead_letter_queue
                WHERE topic = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (topic, limit, offset),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT event_id, topic, payload, callback_id,
                       callback_meta, failure_reason, attempts,
                       total_time_ms, created_at
                FROM dead_letter_queue
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

        results = []
        for row in rows:
            results.append(DeadLetterEntry(
                event_id=row[0],
                topic=row[1],
                payload=json.loads(row[2]),
                callback_id=row[3],
                callback_meta=json.loads(row[4]) if row[4] else {},
                failure_reason=row[5],
                attempts=row[6],
                total_time_ms=row[7],
                created_at=row[8],
            ))
        return results

    def count(self, topic: Optional[str] = None) -> int:
        """返回死信记录总数。"""
        conn = self._get_conn()
        if topic:
            row = conn.execute(
                "SELECT COUNT(*) FROM dead_letter_queue WHERE topic = ?",
                (topic,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM dead_letter_queue"
            ).fetchone()
        return row[0] if row else 0

    # ── 清理 ──────────────────────────────────────────────────────────────

    def purge(self, before_timestamp: float):
        """
        清理指定时间戳之前的死信记录。

        参数:
            before_timestamp: Unix 时间戳，清理该时间之前的所有记录
        """
        conn = self._get_conn()
        with self._lock:
            cursor = conn.execute(
                "DELETE FROM dead_letter_queue WHERE created_at < ?",
                (before_timestamp,),
            )
            conn.commit()
            deleted = cursor.rowcount
        logger.info("死信清理: 删除了 %d 条旧记录（before=%s）", deleted, before_timestamp)
        return deleted
