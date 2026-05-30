"""observability — EventBusMetrics and health_check for the inter-agent event bus.

Three-layer observability (Linus #10):
  Layer 1: Structured logging (JSON-format per operation)
  Layer 2: In-memory metrics with P50/P95/P99 snapshot
  Layer 3: Health-check endpoint data
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional

from event_schema_v2 import SCHEMA_VERSION
from event_schema_v2 import MAX_TTL_SECONDS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# EventBusMetrics — in-memory counters + latency ring buffer
# ---------------------------------------------------------------------------

MAX_LATENCY_SAMPLES = 10000
MAX_LATENCY_WINDOW = 1000  # snapshot uses the last N


@dataclass
class EventBusMetrics:
    """In-memory metrics collector.  Thread-safe via caller serialisation."""

    events_written: int = 0
    events_read: int = 0
    dead_letters: int = 0
    wal_checkpoints: int = 0
    connection_errors: int = 0
    write_latencies: List[float] = field(default_factory=list)
    cursor_lags: Dict[str, int] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock, repr=False)

    def record_write(self, latency_ms: float) -> None:
        """Record a write operation with its latency in milliseconds."""
        with self._lock:
            self.events_written += 1
            self.write_latencies.append(latency_ms)
            # Keep the ring buffer bounded
            if len(self.write_latencies) > MAX_LATENCY_SAMPLES:
                self.write_latencies = self.write_latencies[-MAX_LATENCY_WINDOW:]

    def record_read(self) -> None:
        """Increment read counter."""
        with self._lock:
            self.events_read += 1

    def record_checkpoint(self, success: bool) -> None:
        """Increment checkpoint counter."""
        if success:
            with self._lock:
                self.wal_checkpoints += 1

    def update_cursor_lag(self, consumer_id: str, lag: int) -> None:
        """Record how many events a consumer is behind."""
        with self._lock:
            self.cursor_lags[consumer_id] = lag

    def snapshot(self) -> dict:
        """Return a Prometheus-style snapshot with P50/P95/P99 latencies."""
        latencies = (
            sorted(self.write_latencies[-MAX_LATENCY_WINDOW:])
            if self.write_latencies
            else []
        )
        n = len(latencies)

        def _perc(p: float) -> float:
            if n == 0:
                return 0.0
            idx = int(n * p / 100.0)
            return round(latencies[min(idx, n - 1)], 4)

        return {
            "events_written_total": self.events_written,
            "events_read_total": self.events_read,
            "dead_letters_total": self.dead_letters,
            "wal_checkpoints_total": self.wal_checkpoints,
            "connection_errors_total": self.connection_errors,
            "write_latency_ms": {
                "p50": _perc(50),
                "p95": _perc(95),
                "p99": _perc(99),
            },
            "cursor_lags": dict(self.cursor_lags),
        }


# Global metrics singleton
_metrics: Optional[EventBusMetrics] = None


def get_metrics() -> EventBusMetrics:
    """Return the global EventBusMetrics singleton."""
    global _metrics
    if _metrics is None:
        _metrics = EventBusMetrics()
    return _metrics


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


def health_check(db_path: str) -> dict:
    """Run full health assessment against the event-bus database.

    Checks:
      1. WAL journal mode
      2. Schema version
      3. Unarchived dead-letter backlog
      4. Disk usage percentage

    Returns dict: {status, timestamp, checks, metrics, version}
    """
    overall = "ok"
    checks: dict = {}
    conn: Optional[sqlite3.Connection] = None

    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as exc:
        return {
            "status": "error",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "checks": {"_connect": str(exc)},
            "metrics": get_metrics().snapshot(),
            "version": f"phase1-v{SCHEMA_VERSION}",
        }

    try:
        # 1. WAL status
        try:
            wal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            checks["wal_mode"] = wal_mode
            if wal_mode.lower() != "wal":
                overall = "error"
                checks["wal_mode_error"] = "Expected 'wal', got '%s'" % wal_mode
        except sqlite3.Error as exc:
            checks["wal_mode"] = str(exc)
            overall = "error"

        # 2. Schema version
        try:
            row = conn.execute(
                "SELECT MAX(version) FROM schema_version"
            ).fetchone()
            version = row[0] if row and row[0] is not None else 0
            checks["schema_version"] = version
            if version != SCHEMA_VERSION:
                overall = "warning" if overall == "ok" else overall
                checks["schema_version_warning"] = (
                    f"Expected {SCHEMA_VERSION}, got {version}"
                )
        except sqlite3.OperationalError:
            # schema_version table does not exist yet
            checks["schema_version"] = 0
            overall = "warning" if overall == "ok" else overall
        except sqlite3.Error as exc:
            checks["schema_version"] = str(exc)
            overall = "error"

        # 3. Dead-letter backlog
        try:
            dead_count = conn.execute(
                "SELECT COUNT(*) FROM dead_letters WHERE archived=0"
            ).fetchone()[0]
            checks["unarchived_dead_letters"] = dead_count
            if dead_count > 10000:
                overall = "warning" if overall == "ok" else overall
        except sqlite3.OperationalError:
            checks["unarchived_dead_letters"] = 0
        except sqlite3.Error as exc:
            checks["unarchived_dead_letters"] = str(exc)

        # 4. Disk usage (includes WAL file — Fei-Fei: "WAL文件也计入db大小")
        try:
            stat = os.statvfs(os.path.dirname(db_path))
            disk_usage = round((1.0 - stat.f_bfree / stat.f_blocks) * 100.0, 1)
            checks["disk_usage_percent"] = disk_usage
            # Also report db file + WAL file size
            db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
            wal_path = db_path + "-wal"
            wal_size = os.path.getsize(wal_path) if os.path.exists(wal_path) else 0
            checks["db_size_mb"] = round((db_size + wal_size) / 1024 / 1024, 2)
            if disk_usage > 95:
                overall = "error"
            elif disk_usage > 85:
                overall = "warning" if overall == "ok" else overall
        except (OSError, ZeroDivisionError) as exc:
            checks["disk_usage_percent"] = str(exc)

    finally:
        try:
            conn.close()
        except Exception:
            pass

    metrics = get_metrics()

    return {
        "status": overall,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checks": checks,
        "metrics": metrics.snapshot(),
        "version": f"phase1-v{SCHEMA_VERSION}",
    }
