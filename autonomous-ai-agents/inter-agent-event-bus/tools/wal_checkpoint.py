"""wal_checkpoint — WAL checkpoint background task.

Runs PRAGMA wal_checkpoint(PASSIVE) every 60 seconds on a daemon thread.
Monitors WAL file size — warns at >10 MB, errors at >100 MB.
Uses time.monotonic() for interval timing (Fei-Fei: "防系统时间调整跳checkpoint").
Graceful shutdown via threading.Event + thread.join (Dijkstra: daemon thread must join).

Linus: "SQLite WAL文件长到GB级的事故我见过多次——生产环境致命缺陷"
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import EventBusWriter

logger = logging.getLogger(__name__)


class WalCheckpointTask:
    """Background daemon thread that periodically checkpoints the WAL.

    Usage::

        task = WalCheckpointTask(writer)
        task.start()
        # ... application runs ...
        task.stop()
    """

    CHECKPOINT_INTERVAL: float = 60.0  # seconds (was 30 — Andrej: too aggressive)
    WAL_WARN_BYTES: int = 10 * 1024 * 1024    #  10 MB
    WAL_ERROR_BYTES: int = 100 * 1024 * 1024  # 100 MB

    def __init__(self, writer: EventBusWriter):
        self.writer = writer
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Launch the checkpoint daemon thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="wal-ckpt")
        self._thread.start()
        logger.info("WAL checkpoint task started (interval=%ds)", self.CHECKPOINT_INTERVAL)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal stop and wait for the daemon thread to exit."""
        self._stop.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            if self._thread.is_alive():
                logger.warning("WAL checkpoint thread did not exit within %.1fs", timeout)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _run(self) -> None:
        while not self._stop.wait(self.CHECKPOINT_INTERVAL):
            try:
                self._checkpoint_once()
            except Exception:
                logger.exception("WAL checkpoint iteration failed")

    def _checkpoint_once(self) -> None:
        conn = self.writer.conn
        if conn is None:
            return

        # ---- PRAGMA wal_checkpoint(PASSIVE) ----
        # Dijkstra: TRUNCATE requires exclusive access, breaks WAL concurrency.
        # PASSIVE returns BUSY if readers exist — caller retries next tick.
        try:
            result = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        except Exception as exc:
            logger.error("WAL checkpoint PRAGMA failed: %s", exc)
            return

        if result:
            # result = (busy?, log_frames, checkpointed_frames)
            busy = result[0]
            log_frames = result[1]
            ckpt_frames = result[2]
            if busy == 0:
                logger.debug("WAL checkpoint OK (log=%d, ckpt=%d)", log_frames, ckpt_frames)
            elif busy == 1:
                logger.warning(
                    "WAL checkpoint PASSIVE (reader active), log_frames=%d", log_frames
                )

        # ---- WAL file size monitoring ----
        wal_path = self.writer.db_path + "-wal"
        try:
            if os.path.exists(wal_path):
                wal_size = os.path.getsize(wal_path)
                if wal_size > self.WAL_ERROR_BYTES:
                    logger.error(
                        "WAL file critically oversized: %d bytes (path=%s)",
                        wal_size, wal_path,
                    )
                elif wal_size > self.WAL_WARN_BYTES:
                    logger.warning(
                        "WAL file oversized: %d bytes (path=%s)",
                        wal_size, wal_path,
                    )
        except OSError as exc:
            logger.warning("Could not stat WAL file: %s", exc)
