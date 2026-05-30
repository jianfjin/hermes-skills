"""connection — EventBusReader and EventBusWriter for the inter-agent event bus.

Architecture (v2):
  Writer: global singleton, PRAGMA full-set, one connection for all writes.
  Reader: one per agent, independent sqlite3.Connection, context manager.

No ConnectionPool. No retry decorator. No mmap_size.
Linus: "SQLite connections aren't sockets."
Guido: "Simple is better than complex."
"""

from __future__ import annotations

import logging
import os
import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _resolve_db_path() -> str:
    """Resolve database path from env or default location."""
    path = os.environ.get("EVENT_BUS_DB_PATH")
    if path:
        return path
    default_dir = os.path.join(
        os.path.expanduser("~"), ".hermes", "shared"
    )
    os.makedirs(default_dir, exist_ok=True)
    return os.path.join(default_dir, "event_bus.db")


# ---------------------------------------------------------------------------
# EventBusReader — per-agent read connection
# ---------------------------------------------------------------------------

class EventBusReader:
    """Per-agent read connection with context manager protocol.

    Usage::

        reader = EventBusReader(db_path)
        with reader.acquire() as conn:
            rows = conn.execute("SELECT ...").fetchall()

    Each agent instantiates one Reader.  Connection is lazily created
    on first ``acquire()`` and reused thereafter.  On sqlite3.Error the
    connection is closed and will be rebuilt on next acquire.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _resolve_db_path()
        self._conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open (or re-open) the read connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        # Guido: only busy_timeout — no Python-layer retry
        # Linus: busy handler beats application-layer retry in 90% of cases
        self._conn.execute("PRAGMA busy_timeout=5000")

    @contextmanager
    def acquire(self) -> Iterator[sqlite3.Connection]:
        """Context manager that yields a ready sqlite3.Connection."""
        if self._conn is None:
            self.connect()
        try:
            yield self._conn
        except sqlite3.Error:
            # Connection may be compromised — rebuild next time
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
            raise

    def close(self) -> None:
        """Explicitly close the connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


# ---------------------------------------------------------------------------
# EventBusWriter — global singleton write connection
# ---------------------------------------------------------------------------

class EventBusWriter:
    """Global singleton write connection with full PRAGMA set.

    Exactly ONE writer exists per process.  It holds the WAL write
    privileges and is the authority for schema migrations.

    PRAGMA set:
      journal_mode=WAL      — concurrent reads + serialised writes
      synchronous=NORMAL    — safe with WAL, not FULL
      cache_size=-8000      — 8 MB page cache (negative = KB)
      busy_timeout=5000     — 5 s busy-wait at C level
      page_size=4096        — standard 4K pages
      temp_store=MEMORY     — temporary tables/indices in RAM
      foreign_keys=ON       — referential integrity

    Explicitly NOT set:
      mmap_size             — removed per Linus review (OOM risk on small VMs)
    """

    _instance: Optional[EventBusWriter] = None
    _lock = threading.Lock()
    write_lock = threading.Lock()  # serialises Python-level write access (thread safety)
    COMMIT_MAX_RETRIES = 3

    def __new__(cls, db_path: Optional[str] = None) -> EventBusWriter:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    obj = super().__new__(cls)
                    obj.db_path = db_path or _resolve_db_path()
                    obj._conn: Optional[sqlite3.Connection] = None
                    cls._instance = obj
        return cls._instance

    def connect(self) -> None:
        """Open the writer connection with full PRAGMA block."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row  # enable dict-style access (publish_event needs this)
        cur = self._conn.cursor()
        cur.executescript("""
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=NORMAL;
            PRAGMA cache_size=-8000;
            PRAGMA busy_timeout=5000;
            PRAGMA page_size=4096;
            PRAGMA temp_store=MEMORY;
            PRAGMA foreign_keys=ON;
        """)
        # mmap_size intentionally not set — Linus: OOM risk on 1.9 GB VMs

    # -- Andrej: commit with retry on SQLITE_BUSY --
    def commit_with_retry(self) -> None:
        """Commit with up to COMMIT_MAX_RETRIES on sqlite3.OperationalError.

        SQLite busy_timeout handles contention at C level but some edge
        cases (e.g. checkpoint holding a read-lock) still surface as
        OperationalError at commit time.  A short retry loop absorbs these.
        """
        if self._conn is None:
            return
        for attempt in range(1, self.COMMIT_MAX_RETRIES + 1):
            try:
                self._conn.commit()
                return
            except sqlite3.OperationalError:
                if attempt == self.COMMIT_MAX_RETRIES:
                    raise
                logger.debug("Commit retry %d/%d", attempt, self.COMMIT_MAX_RETRIES)
                time.sleep(0.1 * attempt)

    @property
    def conn(self) -> Optional[sqlite3.Connection]:
        return self._conn

    def __enter__(self) -> EventBusWriter:
        """Context-manager entry: ensures a connection is open."""
        if self._conn is None:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context-manager exit.

        Dijkstra: propagate ALL exceptions — never swallow.
        If close() fails we log and let the original exception surface;
        a failed close must NOT mask the real error.
        """
        if exc_type is not None:
            # Exception in body — close is best-effort, don't mask
            try:
                self._conn.close()
            except Exception:
                logger.warning("Writer close failed during exception unwind — ignoring", exc_info=True)
            self._conn = None
            return False  # propagate original exception
        # Normal exit — commit and close
        # (commit_with_retry is called explicitly by callers; __exit__ does not auto-commit)
        return False

    def close(self) -> None:
        """Explicitly close the writer connection."""
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None
