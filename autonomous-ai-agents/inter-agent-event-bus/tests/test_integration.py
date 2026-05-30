#!/usr/bin/env python3
"""Integration tests for the inter-agent event bus.

Tests publish, subscribe, wildcard matching, multi-topic cursors,
TTL expiry, error handling, status, concurrent access, and empty results.
Every test uses a fresh shared in-memory SQLite database
(``file::memory:?cache=shared``) so no filesystem state leaks between tests.
"""

from __future__ import annotations

import importlib.util
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Module loaders (hyphens in the skill path prevent normal imports)
# ---------------------------------------------------------------------------

_SKILL_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..")
)
_TOOLS_DIR = os.path.join(_SKILL_DIR, "tools")


def _load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_publish_mod = _load_module("publish_event", os.path.join(_TOOLS_DIR, "publish_event.py"))
_subscribe_mod = _load_module("subscribe_events", os.path.join(_TOOLS_DIR, "subscribe_events.py"))
_status_mod = _load_module("event_bus_status", os.path.join(_TOOLS_DIR, "event_bus_status.py"))

publish_event = _publish_mod.publish_event
subscribe_events = _subscribe_mod.subscribe_events
event_bus_status = _status_mod.event_bus_status

# ---------------------------------------------------------------------------
# Shared in-memory database helpers
# ---------------------------------------------------------------------------

_SHARED_MEM = "file::memory:?cache=shared"

# Unified schema that satisfies both publish_event's and subscribe_events's
# table definitions — superset of all columns from both modules.
_UNIFIED_EVENTS_DDL = """
CREATE TABLE IF NOT EXISTS events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT    NOT NULL UNIQUE,
    topic           TEXT    NOT NULL,
    schema_version  TEXT    NOT NULL DEFAULT '1.0',
    publisher       TEXT    NOT NULL DEFAULT '',
    payload         TEXT    NOT NULL,
    ttl_seconds     INTEGER NOT NULL DEFAULT 86400,
    ttl             INTEGER NOT NULL DEFAULT 86400,
    created_at      REAL    NOT NULL,
    expires_at      REAL    NOT NULL DEFAULT 0
);
"""

_CURSORS_DDL = """
CREATE TABLE IF NOT EXISTS cursors (
    agent_id       TEXT NOT NULL,
    topic_pattern  TEXT NOT NULL,
    last_event_id  INTEGER NOT NULL DEFAULT 0,
    updated_at     REAL  NOT NULL DEFAULT (julianday('now')),
    PRIMARY KEY (agent_id, topic_pattern)
);
"""


def _reset_state() -> None:
    """Reset all module singletons to force a fresh shared in-memory DB."""
    # --- publish_event ---
    _publish_mod._db_conn = None
    _publish_mod._db_path = _SHARED_MEM
    # --- subscribe_events ---
    _subscribe_mod.DB_PATH = _SHARED_MEM
    # --- event_bus_status ---
    _status_mod.DB_PATH = _SHARED_MEM
    # Nuke thread-local connections held by subscribe / status
    for m in (_subscribe_mod, _status_mod):
        if hasattr(m, "_local"):
            try:
                del m._local.conn
            except AttributeError:
                pass
    # Open a temporary connection to prime the shared in-memory schema
    conn = sqlite3.connect(_SHARED_MEM, check_same_thread=False)
    conn.executescript(_UNIFIED_EVENTS_DDL)
    conn.executescript(_CURSORS_DDL)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_publish_subscribe_full_flow():
    """publish a feifei event, then subscribe with matching pattern."""
    _reset_state()
    r = publish_event(topic="feifei:moan", payload={"volume": 8})
    assert r["status"] == "published"
    assert r["topic"] == "feifei:moan"

    events = subscribe_events(topic_pattern="feifei:moan", max_events=10)
    assert len(events) == 1
    assert events[0]["topic"] == "feifei:moan"
    assert '"volume": 8' in events[0]["payload"] or 8 in str(events[0]["payload"])

    print("  [PASS] test_publish_subscribe_full_flow")


def test_wildcard_matching():
    """Wildcard feifei:* matches all feifei: subtopics."""
    _reset_state()
    publish_event(topic="feifei:whisper", payload={"msg": "harder"})
    publish_event(topic="feifei:scream", payload={"msg": "faster"})
    publish_event(topic="andrew:coach", payload={"msg": "keep going"})

    events = subscribe_events(topic_pattern="feifei:*", max_events=10)
    assert len(events) == 2
    topics = {e["topic"] for e in events}
    assert topics == {"feifei:whisper", "feifei:scream"}

    print("  [PASS] test_wildcard_matching")


def test_multi_topic_cursors():
    """Two independent subscriptions don't lose events between them."""
    _reset_state()
    publish_event(topic="feifei:a", payload={"n": 1})
    publish_event(topic="feifei:b", payload={"n": 2})
    publish_event(topic="feifei:a", payload={"n": 3})

    # Subscribe to both topics from different agents
    a_events = subscribe_events(topic_pattern="feifei:a", agent_id="agent_a", max_events=10)
    b_events = subscribe_events(topic_pattern="feifei:b", agent_id="agent_b", max_events=10)

    assert len(a_events) == 2, f"expected 2 for agent_a, got {len(a_events)}"
    assert len(b_events) == 1, f"expected 1 for agent_b, got {len(b_events)}"

    # Second poll for agent_a should return nothing (cursor advanced)
    a_events2 = subscribe_events(topic_pattern="feifei:a", agent_id="agent_a", max_events=10)
    assert len(a_events2) == 0, f"expected 0 on re-poll, got {len(a_events2)}"

    print("  [PASS] test_multi_topic_cursors")


def test_ttl_expiry_cleanup():
    """Events past their TTL are not returned and cleanup runs."""
    _reset_state()
    # publish with a 0-second TTL so it expires immediately
    r = publish_event(topic="feifei:quickie", payload={"o": "h"}, ttl_seconds=0)
    # give the GC a moment — publish removes expired rows
    time.sleep(0.05)

    events = subscribe_events(topic_pattern="feifei:quickie", max_events=10)
    assert len(events) == 0, f"expired event should be invisible, got {len(events)}"

    # Also verify status reports zero events
    st = event_bus_status()
    assert st["total_events"] == 0, f"expected 0 events after expiry, got {st['total_events']}"

    print("  [PASS] test_ttl_expiry_cleanup")


def test_invalid_topic_rejected():
    """Publish raises ValueError for badly-formed topics."""
    _reset_state()
    for bad in ("INVALID", "no-colon", ":", "a:", ":b", "a b:c", "feifei: "):
        try:
            publish_event(topic=bad)
            assert False, f"expected ValueError for {bad!r}"
        except ValueError:
            pass

    print("  [PASS] test_invalid_topic_rejected")


def test_event_bus_status():
    """event_bus_status returns accurate aggregate metrics."""
    _reset_state()
    st = event_bus_status()
    assert st["total_events"] == 0
    assert st["active_cursors"] == 0
    assert st["topic_histogram"] == {}

    publish_event(topic="feifei:gasp", payload={"x": 1})
    publish_event(topic="feifei:gasp", payload={"x": 2})
    publish_event(topic="andrew:nod", payload={"y": 3})

    st = event_bus_status()
    assert st["total_events"] == 3
    assert st["topic_histogram"] == {"feifei:gasp": 2, "andrew:nod": 1}
    assert st["active_cursors"] == 0  # no subscribe calls yet

    # Subscribe creates a cursor
    subscribe_events(topic_pattern="feifei:*", agent_id="feifei", max_events=10)
    st = event_bus_status()
    assert st["active_cursors"] >= 1

    print("  [PASS] test_event_bus_status")


def test_concurrent_publish_subscribe():
    """Publish and subscribe from multiple threads without data loss."""
    _reset_state()
    n_threads = 5
    events_per = 3
    barrier = threading.Barrier(n_threads)
    published_ids: List[str] = []
    pub_lock = threading.Lock()

    def publisher(tid: int):
        barrier.wait()
        for i in range(events_per):
            r = publish_event(
                topic="feifei:thrust",
                payload={"tid": tid, "i": i},
            )
            with pub_lock:
                published_ids.append(r["event_id"])

    threads = [threading.Thread(target=publisher, args=(tid,)) for tid in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Subscribe to collect everything
    all_events = subscribe_events(topic_pattern="feifei:*", max_events=n_threads * events_per + 5)
    assert len(all_events) == n_threads * events_per, (
        f"expected {n_threads * events_per} events, got {len(all_events)}"
    )

    print("  [PASS] test_concurrent_publish_subscribe")


def test_empty_results():
    """Subscribe with no matching events returns empty list."""
    _reset_state()
    events = subscribe_events(topic_pattern="feifei:*", max_events=10)
    assert events == [], f"expected [], got {events}"

    # After publishing one non-matching event
    publish_event(topic="andrew:laugh", payload={"ha": 3})
    events = subscribe_events(topic_pattern="feifei:*", max_events=10)
    assert events == [], "non-matching topic should not appear"

    print("  [PASS] test_empty_results")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    tests = [
        ("publish -> subscribe full flow", test_publish_subscribe_full_flow),
        ("wildcard feifei:* matching", test_wildcard_matching),
        ("multi-topic cursors", test_multi_topic_cursors),
        ("TTL expiry & cleanup", test_ttl_expiry_cleanup),
        ("invalid topic rejection", test_invalid_topic_rejected),
        ("event_bus_status stats", test_event_bus_status),
        ("concurrent publish+subscribe", test_concurrent_publish_subscribe),
        ("empty results", test_empty_results),
    ]
    total = len(tests)
    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except Exception as exc:
            failed += 1
            import traceback
            print(f"  [FAIL] {name}: {exc}")
            traceback.print_exc()
    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed, {failed}/{total} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
