#!/usr/bin/env python3
"""Subscribe to events from the inter-agent event bus.

Each (consumer_id) pair maintains an independent cursor via the
consumer_cursors table for at-least-once delivery.

Schema is owned by event_schema_v2.py — do not create any tables here.
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# -- path setup --
_SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_TOOLS_DIR = os.path.join(_SKILL_DIR, "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from connection import EventBusReader  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SHARED_DIR = os.path.join(os.path.expanduser("~"), ".hermes", "shared")
os.makedirs(_SHARED_DIR, exist_ok=True)
DB_PATH = os.environ.get("EVENT_BUS_DB_PATH") or os.path.join(_SHARED_DIR, "event_bus.db")

_EVENT_TYPE_RE = re.compile(
    r"^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$|^[a-z][a-z0-9_-]*:\*$|^\*$"
)

# Per-thread reader cache
_reader: EventBusReader | None = None


def _get_reader() -> EventBusReader:
    """Return a thread-local EventBusReader."""
    global _reader
    if _reader is None:
        _reader = EventBusReader(DB_PATH)
    return _reader


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def subscribe_events(
    event_type_pattern: str,
    consumer_id: str = "default",
    since_event_id: int = 0,
    max_events: int = 10,
    block_seconds: int = 0,
) -> List[Dict[str, Any]]:
    """Fetch new events matching *event_type_pattern* for *consumer_id*.

    Uses consumer_cursors.last_event_id for incremental reads (cursor is
    an INTEGER PRIMARY KEY — event_id, not UUID).

    Parameters
    ----------
    event_type_pattern:
        Category:name wildcard, e.g. ``agent:*`` or ``*``.
    consumer_id:
        Unique consumer identifier for cursor tracking.
    since_event_id:
        Minimum event_id to read from (0 = use stored cursor).
    max_events:
        Maximum events to return (1-100).
    block_seconds:
        If > 0, block up to this many seconds waiting for events.

    Returns
    -------
    list[dict]
        ``[{event_id, event_type, payload, source_agent, created_at, status}, ...]``
    """
    if not event_type_pattern or len(event_type_pattern) > 256:
        raise ValueError(f"event_type_pattern length 1-256, got {len(event_type_pattern)}")
    if not _EVENT_TYPE_RE.match(event_type_pattern):
        raise ValueError(f"Invalid pattern {event_type_pattern!r}")
    if not 1 <= max_events <= 100:
        raise ValueError(f"max_events 1-100, got {max_events}")
    if block_seconds < 0:
        raise ValueError(f"block_seconds >= 0, got {block_seconds}")

    reader = _get_reader()
    like = event_type_pattern.replace("*", "%")
    deadline = time.time() + block_seconds if block_seconds > 0 else None

    # ---- Resolve cursor ----
    if since_event_id <= 0:
        try:
            with reader.acquire() as conn:
                row = conn.execute(
                    "SELECT last_event_id FROM consumer_cursors WHERE consumer_id=?",
                    (consumer_id,),
                ).fetchone()
        except Exception:
            row = None
        since_event_id = int(row["last_event_id"]) if row and row["last_event_id"] else 0

    # ---- Poll loop ----
    results: List[Dict[str, Any]] = []
    while True:
        try:
            with reader.acquire() as conn:
                rows = conn.execute(
                    "SELECT event_id, source_agent, event_type, payload, "
                    "       created_at, status "
                    "FROM events "
                    "WHERE event_id > ? AND event_type LIKE ? "
                    "ORDER BY event_id ASC LIMIT ?",
                    (since_event_id, like, max_events),
                ).fetchall()
        except Exception:
            rows = []

        if rows:
            for r in rows:
                results.append({
                    "event_id": r["event_id"],
                    "source_agent": r["source_agent"],
                    "event_type": r["event_type"],
                    "payload": r["payload"],
                    "created_at": r["created_at"],
                    "status": r["status"],
                })
            break

        if deadline is None or time.time() >= deadline:
            break
        time.sleep(0.1)

    # ---- Update cursor ----
    if results:
        try:
            with reader.acquire() as conn:
                conn.execute(
                    "INSERT INTO consumer_cursors(consumer_id, last_event_id, updated_at) "
                    "VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now')) "
                    "ON CONFLICT(consumer_id) DO UPDATE SET "
                    "  last_event_id=excluded.last_event_id, "
                    "  updated_at=excluded.updated_at",
                    (consumer_id, results[-1]["event_id"]),
                )
                conn.commit()
        except Exception:
            pass

    # ---- Metrics ----
    if results:
        try:
            from observability import get_metrics

            metrics = get_metrics()
            metrics.record_read()
            # update cursor lag
            try:
                with reader.acquire() as conn:
                    max_id_row = conn.execute(
                        "SELECT MAX(event_id) FROM events"
                    ).fetchone()
                    if max_id_row and max_id_row[0] is not None:
                        lag = max_id_row[0] - results[-1]["event_id"]
                        metrics.update_cursor_lag(consumer_id, lag)
            except Exception:
                pass
        except Exception:
            pass

    return results
