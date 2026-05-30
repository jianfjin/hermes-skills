#!/usr/bin/env python3
"""Observability tool for the inter-agent event bus.

Returns total event count, active consumer count, topic histogram,
plus v2 fields: schema_version, wal_mode, dead_letter_count, disk_usage.

Uses EventBusMetrics for in-memory stats and health_check() for
database-level assessment.
"""

from __future__ import annotations

import logging
import os
import sys
import time
from typing import Any, Dict

logger = logging.getLogger(__name__)

_skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tools_dir = os.path.join(_skill_dir, "tools")
if _tools_dir not in sys.path:
    sys.path.insert(0, _tools_dir)

from connection import EventBusReader  # noqa: E402
from event_schema_v2 import SCHEMA_VERSION  # noqa: E402
from observability import get_metrics, health_check  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SHARED_DIR = os.path.join(os.path.expanduser("~"), ".hermes", "shared")
os.makedirs(_SHARED_DIR, exist_ok=True)
DB_PATH = os.environ.get("EVENT_BUS_DB_PATH") or os.path.join(_SHARED_DIR, "event_bus.db")

_reader: EventBusReader | None = None


def _get_reader() -> EventBusReader:
    global _reader
    if _reader is None:
        _reader = EventBusReader(DB_PATH)
    return _reader


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def event_bus_status() -> Dict[str, Any]:
    """Return aggregate bus health metrics.

    Returns dict with v2 fields:
      total_events, active_consumers, event_type_histogram,
      schema_version, wal_mode, dead_letter_count,
      disk_usage_percent, db_path, health, metrics.
    """
    reader = _get_reader()
    now = time.time()

    status: Dict[str, Any] = {
        "total_events": 0,
        "active_consumers": 0,
        "event_type_histogram": {},
        "schema_version": SCHEMA_VERSION,
        "wal_mode": "unknown",
        "dead_letter_count": 0,
        "disk_usage_percent": 0.0,
        "db_path": DB_PATH,
    }

    try:
        with reader.acquire() as conn:
            # Total events
            row = conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()
            status["total_events"] = row["c"] if row else 0

            # Active consumers
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM consumer_cursors"
            ).fetchone()
            status["active_consumers"] = row["c"] if row else 0

            # Event type histogram
            rows = conn.execute(
                "SELECT event_type, COUNT(*) AS c FROM events "
                "GROUP BY event_type ORDER BY c DESC"
            ).fetchall()
            status["event_type_histogram"] = {
                r["event_type"]: r["c"] for r in rows
            }

            # WAL mode
            wal_row = conn.execute("PRAGMA journal_mode").fetchone()
            status["wal_mode"] = wal_row[0] if wal_row else "unknown"

            # Dead letter count
            try:
                dl_row = conn.execute(
                    "SELECT COUNT(*) AS c FROM dead_letters WHERE archived=0"
                ).fetchone()
                status["dead_letter_count"] = dl_row["c"] if dl_row else 0
            except Exception:
                status["dead_letter_count"] = 0

    except Exception as exc:
        logger.warning("event_bus_status DB error: %s", exc)
        status["_error"] = str(exc)

    # Disk usage
    try:
        stat = os.statvfs(os.path.dirname(DB_PATH))
        status["disk_usage_percent"] = round(
            (1.0 - stat.f_bfree / stat.f_blocks) * 100.0, 1
        )
    except Exception:
        status["disk_usage_percent"] = 0.0

    # Health check (full assessment)
    try:
        status["health"] = health_check(DB_PATH)
    except Exception as exc:
        status["health"] = {"status": "error", "error": str(exc)}

    # In-memory metrics snapshot
    try:
        status["metrics"] = get_metrics().snapshot()
    except Exception:
        status["metrics"] = {}

    return status
