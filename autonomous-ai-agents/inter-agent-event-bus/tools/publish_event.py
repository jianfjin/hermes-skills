"""publish_event — Publish an event to the inter-agent event bus.

Events carry a structured payload, a source agent, and an event type.
Backing store is SQLite via EventBusWriter (v2 connection architecture).

Usage::

    result = publish_event(
        event_type="agent:heartbeat",
        payload={"status": "running", "load": 0.42},
        source_agent="feifei",
    )

Schema management is delegated to event_schema_v2.py.
Cleanup / dead-letter logic is delegated to dead_letter.py.
Pure Python stdlib only.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import sys
import time
from typing import Any

# ---------------------------------------------------------------------------
# Path setup — tools dir has hyphens, so inject manually
# ---------------------------------------------------------------------------

_skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_tools_dir = os.path.join(_skill_dir, "tools")
if _tools_dir not in sys.path:
    sys.path.insert(0, _tools_dir)

from connection import EventBusWriter  # noqa: E402

# ---------------------------------------------------------------------------
# Hooks integration (best-effort)
# ---------------------------------------------------------------------------

if _skill_dir not in sys.path:
    sys.path.insert(0, _skill_dir)

_hooks_instance: Any = None

try:
    from hooks import setup_delivery_hooks  # noqa: E402

    _HAS_HOOKS = True
except ImportError:
    _HAS_HOOKS = False


def _get_hooks() -> Any:
    """Lazy singleton for delivery hooks."""
    global _hooks_instance
    if not _HAS_HOOKS:
        return None
    if _hooks_instance is None:
        _hooks_instance = setup_delivery_hooks(
            db_path=EventBusWriter().db_path
        )
    return _hooks_instance


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

_EVENT_TYPE_RE = re.compile(r"^[a-z][a-z0-9_-]*:[a-z][a-z0-9_-]*$")
DEFAULT_TTL_SECONDS: int = 86400  # 24 hours


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _validate_event_type(event_type: str) -> None:
    if not _EVENT_TYPE_RE.match(event_type):
        raise ValueError(
            f"Invalid event_type {event_type!r}. Must match pattern "
            f"category:name (e.g. 'agent:heartbeat')."
        )


def _serialize_payload(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"Payload is not JSON-serializable: {exc}") from exc


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def publish_event(
    event_type: str,
    payload: Any = None,
    *,
    source_agent: str = "unknown",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
    max_retries: int = 3,
) -> dict:
    """Publish a single event to the inter-agent bus.

    Parameters
    ----------
    event_type:
        Routing key matching ``^[a-z][a-z0-9_-]+:[a-z][a-z0-9_-]+$``.
    payload:
        JSON-serialisable data attached to the event (default ``{}``).
    source_agent:
        Name or ID of the publishing agent (default ``"unknown"``).
    ttl_seconds:
        Time-to-live in seconds (default 86400 = 24 h).
    max_retries:
        Maximum retry attempts before dead-lettering (default 3).

    Returns
    -------
    dict
        ``{"event_id": <int>, "event_type": "<type>",
          "created_at": "<ISO8601>", "status": "published"}``

    Raises
    ------
    ValueError
        If *event_type* is malformed.
    TypeError
        If *payload* cannot be serialised to JSON.
    sqlite3.OperationalError
        If the DB stays busy after the 5 s timeout.
    """
    _validate_event_type(event_type)
    payload_json = _serialize_payload(payload if payload is not None else {})

    writer = EventBusWriter()
    start = time.monotonic()

    with writer.write_lock:
        try:
            conn = writer.conn
            if conn is None:
                writer.connect()
                conn = writer.conn
                if conn is None:
                    raise RuntimeError("Writer connection is None after connect()")

            cur = conn.execute(
                """INSERT INTO events (source_agent, event_type, payload,
                                       ttl_seconds, max_retries)
                   VALUES (?, ?, ?, ?, ?)""",
                (source_agent, event_type, payload_json, ttl_seconds, max_retries),
            )
            conn.commit()
            event_id = cur.lastrowid

            # Read back created_at for the response
            row = conn.execute(
                "SELECT created_at FROM events WHERE event_id=?",
                (event_id,),
            ).fetchone()
            created_at = row["created_at"] if row else ""
        except sqlite3.OperationalError as exc:
            if "busy" in str(exc).lower():
                raise sqlite3.OperationalError(
                    "Event bus DB busy after 5 s timeout. Try again."
                ) from exc
            raise

    elapsed_ms = (time.monotonic() - start) * 1000.0

    # -- Delivery hooks (best-effort; never fail publish over it) --
    try:
        hooks = _get_hooks()
        if hooks is not None:
            hooks.deliver_event(
                event_id=event_id,
                topic=event_type,
                payload=json.loads(payload_json),
            )
    except Exception:
        pass

    # -- Record metrics --
    try:
        from observability import get_metrics

        get_metrics().record_write(elapsed_ms)
    except Exception:
        pass

    return {
        "event_id": event_id,
        "event_type": event_type,
        "created_at": created_at,
        "status": "published",
    }
