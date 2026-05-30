#!/usr/bin/env python3
"""Phase 1 v2 集成测试套件 — 9大场景, 2,000+行事件吞吐验证"""

import json
import logging
import os
import sqlite3
import sys
import threading
import time
import traceback

logging.basicConfig(level=logging.CRITICAL, format="%(levelname)s|%(message)s")

SKILL_DIR = os.path.expanduser("~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus")
TOOLS_DIR = os.path.join(SKILL_DIR, "tools")
SCRIPTS_DIR = os.path.join(SKILL_DIR, "scripts")
TEST_DB = "/tmp/hermes_event_bus_test.db"

# Set env BEFORE module-level imports (subscribe_events reads DB_PATH at import time)
os.environ["EVENT_BUS_DB_PATH"] = TEST_DB

# Clean previous test DB
for f in [TEST_DB, TEST_DB + "-wal", TEST_DB + "-shm"]:
    try: os.remove(f)
    except FileNotFoundError: pass

sys.path.insert(0, TOOLS_DIR)
sys.path.insert(0, SKILL_DIR)

from connection import EventBusWriter, EventBusReader
from event_schema_v2 import run_migrations, SCHEMA_VERSION, MAX_TTL_SECONDS
from wal_checkpoint import WalCheckpointTask
from nfs_check import check_filesystem_type, FilesystemNotSupportedError
from observability import get_metrics, health_check, EventBusMetrics
from dead_letter import migrate_to_dead_letter, migrate_expired_events, archive_overflow

import publish_event
from subscribe_events import subscribe_events

# ----------------------------------------------------------------
# Test harness
# ----------------------------------------------------------------
PASS = 0
FAIL = 0
ERRORS = []

def test(name):
    global PASS, FAIL
    def decorator(fn):
        def wrapper():
            global PASS, FAIL
            # Clean DB before each test
            for f in [TEST_DB, TEST_DB + "-wal", TEST_DB + "-shm"]:
                try: os.remove(f)
                except FileNotFoundError: pass
            print(f"  [{name}] ", end="", flush=True)
            try:
                fn()
                PASS += 1
                print("PASS")
            except Exception as e:
                FAIL += 1
                ERRORS.append(f"  FAIL:{name} — {e}")
                traceback.print_exc()
                print(f"FAIL — {e}")
            finally:
                # Clean DB and reset all singletons after each test
                try:
                    w = EventBusWriter()
                    if w and w.conn:
                        w.conn.close()
                    EventBusWriter._instance = None
                except Exception:
                    pass
                # Reset reader singleton (subscribe_events caches it)
                try:
                    from subscribe_events import _get_reader
                    import subscribe_events as _se_mod
                    _se_mod._reader = None
                except Exception:
                    pass
                for f in [TEST_DB, TEST_DB + "-wal", TEST_DB + "-shm"]:
                    try: os.remove(f)
                    except FileNotFoundError: pass
        return wrapper
    return decorator

def setup_db():
    os.environ["EVENT_BUS_DB_PATH"] = TEST_DB
    writer = EventBusWriter(TEST_DB)
    writer.connect()
    run_migrations(writer)
    return writer

def teardown_db():
    for f in [TEST_DB, TEST_DB + "-wal", TEST_DB + "-shm"]:
        try: os.remove(f)
        except FileNotFoundError: pass

# ----------------------------------------------------------------
# Test 1: Schema & Migration
# ----------------------------------------------------------------
@test("Schema creation + migration")
def test_schema():
    w = setup_db()
    conn = w.conn
    # Verify all tables exist
    tables = set()
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        tables.add(row[0])
    assert "events" in tables, f"events table missing: {tables}"
    assert "consumer_cursors" in tables, f"consumer_cursors missing: {tables}"
    assert "dead_letters" in tables, f"dead_letters missing: {tables}"
    assert "schema_version" in tables, f"schema_version missing: {tables}"
    # Verify schema version
    ver = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert ver == SCHEMA_VERSION, f"Schema version mismatch: {ver} vs {SCHEMA_VERSION}"
    # Verify indexes
    indexes = set()
    for row in conn.execute("SELECT name FROM sqlite_master WHERE type='index'").fetchall():
        indexes.add(row[0])
    assert "idx_events_status" in indexes
    assert "idx_events_created" in indexes
    assert "idx_dead_letters_archived" in indexes
    # Verify event_id is not AUTOINCREMENT (Guido fix)
    ddl = conn.execute("SELECT sql FROM sqlite_master WHERE name='events'").fetchone()[0]
    assert "AUTOINCREMENT" not in ddl.upper(), f"AUTOINCREMENT found in DDL: {ddl}"
    # Verify MAX_TTL_SECONDS
    assert MAX_TTL_SECONDS == 86400
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 2: Writer singleton + read-write cycle
# ----------------------------------------------------------------
@test("Writer singleton + publish+subscribe cycle")
def test_write_read():
    w = setup_db()
    publish_event.publish_event(
        event_type="test:ping",
        payload={"msg": "hello world"},
        source_agent="tester",
    )
    events = subscribe_events(
        event_type_pattern="test:ping",
        consumer_id="test-consumer",
        max_events=10,
    )
    assert len(events) == 1, f"Expected 1 event, got {len(events)}"
    e = events[0]
    assert e["event_type"] == "test:ping"
    assert e["source_agent"] == "tester"
    payload = json.loads(e["payload"])
    assert payload["msg"] == "hello world"
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 3: Cursor — second read returns only new events
# ----------------------------------------------------------------
@test("Cursor — incremental reads")
def test_cursor():
    w = setup_db()
    for i in range(5):
        publish_event.publish_event(
            event_type="test:data",
            payload={"seq": i},
            source_agent="tester",
        )
    # First read: get all 5
    first = subscribe_events(
        event_type_pattern="test:data",
        consumer_id="cursor-test",
        max_events=10,
    )
    assert len(first) == 5, f"First read: expected 5, got {len(first)}"
    assert first[-1]["event_id"] == 5  # last event_id

    # Second read with same consumer: should return 0 new
    second = subscribe_events(
        event_type_pattern="test:data",
        consumer_id="cursor-test",
        max_events=10,
    )
    assert len(second) == 0, f"Second read: expected 0, got {len(second)}"

    # Publish 3 more
    for i in range(5, 8):
        publish_event.publish_event(
            event_type="test:data",
            payload={"seq": i},
            source_agent="tester",
        )

    # Third read: should get 3 new
    third = subscribe_events(
        event_type_pattern="test:data",
        consumer_id="cursor-test",
        max_events=10,
    )
    assert len(third) == 3, f"Third read: expected 3, got {len(third)}"
    assert third[0]["event_id"] == 6
    assert third[-1]["event_id"] == 8
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 4: Multiple independent consumers
# ----------------------------------------------------------------
@test("Multiple consumers — independent cursors")
def test_multi_consumer():
    w = setup_db()
    for i in range(10):
        publish_event.publish_event(
            event_type="test:multi",
            payload={"seq": i},
            source_agent="tester",
        )

    # Consumer A reads 5
    a1 = subscribe_events("test:multi", "consumer-a", max_events=5)
    assert len(a1) == 5

    # Consumer B reads all 10
    b1 = subscribe_events("test:multi", "consumer-b", max_events=10)
    assert len(b1) == 10

    # Consumer A reads next 5
    a2 = subscribe_events("test:multi", "consumer-a", max_events=10)
    assert len(a2) == 5

    # Consumer A should now have nothing new
    a3 = subscribe_events("test:multi", "consumer-a", max_events=10)
    assert len(a3) == 0

    # Verify no overlap
    a_ids = [e["event_id"] for e in a1 + a2]
    assert a_ids == list(range(1, 11)), f"A events not contiguous: {a_ids}"
    b_ids = [e["event_id"] for e in b1]
    assert b_ids == list(range(1, 11)), f"B events not contiguous: {b_ids}"
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 5: 5-agent parallel writes (no SQLITE_BUSY)
# ----------------------------------------------------------------
@test("5-agent parallel writes — 0 SQLITE_BUSY")
def test_parallel():
    w = setup_db()
    N_WRITERS = 5
    EVENTS_PER = 200
    errors = []
    lock = threading.Lock()
    event_ids = []

    def writer_task(agent_id, count):
        for i in range(count):
            try:
                result = publish_event.publish_event(
                    event_type=f"agent:{agent_id}",
                    payload={"seq": i, "agent": agent_id},
                    source_agent=agent_id,
                )
                with lock:
                    event_ids.append(result["event_id"])
            except sqlite3.OperationalError as e:
                with lock:
                    errors.append(f"{agent_id}:{i}:{e}")
            except Exception as e:
                with lock:
                    errors.append(f"{agent_id}:{i}:{type(e).__name__}:{e}")

    threads = []
    for aid in range(N_WRITERS):
        t = threading.Thread(target=writer_task, args=(f"writer-{aid}", EVENTS_PER))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Errors during parallel write: {errors}"
    expected = N_WRITERS * EVENTS_PER
    assert len(event_ids) == expected, f"Expected {expected} events, got {len(event_ids)}"

    # Verify all events readable (batch read since max_events <= 100)
    all_events = []
    cursor = 0
    while True:
        batch = subscribe_events("*", "parallel-test", since_event_id=cursor, max_events=100)
        if not batch:
            break
        all_events.extend(batch)
        cursor = batch[-1]["event_id"]
    assert len(all_events) == expected, f"Read back {len(all_events)} vs {expected}"
    print(f" ({expected} events in {N_WRITERS} parallel writers)", end="")
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 6: WAL Checkpoint task
# ----------------------------------------------------------------
@test("WAL checkpoint — task lifecycle")
def test_wal_checkpoint():
    w = setup_db()
    task = WalCheckpointTask(w)
    task.start()
    time.sleep(0.5)  # Let it run a tick
    task.stop(timeout=3.0)
    # Verify thread stopped
    assert task._thread is None or not task._thread.is_alive(), "Thread still alive after stop"
    w.conn.close()
    teardown_db()

@test("WAL checkpoint — persistent across writes")
def test_wal_persistent():
    """Write events, run checkpoint, verify events remain readable."""
    w = setup_db()
    publish_event.publish_event(event_type="test:before", payload={"n": 1}, source_agent="tester")
    task = WalCheckpointTask(w)
    task.start()
    for i in range(50):
        publish_event.publish_event(event_type="test:during", payload={"n": i}, source_agent="tester")
    time.sleep(0.5)
    task.stop(timeout=3.0)
    events = subscribe_events("*", "wal-test", max_events=100)
    assert len(events) >= 50, f"Events lost after checkpoint: {len(events)}"
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 7: NFS check (on local FS, should pass)
# ----------------------------------------------------------------
@test("NFS check — local FS passes")
def test_nfs_pass():
    check_filesystem_type("/tmp")
    # Should not raise — pass

@test("NFS check — FilesystemNotSupportedError defined")
def test_nfs_exception():
    err = FilesystemNotSupportedError("/mnt/nfs", "nfs4")
    assert "nfs4" in str(err)
    assert "NFS" in str(err)

# ----------------------------------------------------------------
# Test 8: Dead letter + expired events
# ----------------------------------------------------------------
@test("Dead letter — migrate single event")
def test_deadletter_migrate():
    w = setup_db()
    publish_event.publish_event(event_type="test:dl", payload={"x": 1}, source_agent="tester")
    migrate_to_dead_letter(w, event_id=1, reason="TEST_FAILURE", consumer_id="tester")
    conn = w.conn
    row = conn.execute("SELECT status FROM events WHERE event_id=1").fetchone()
    assert row["status"] == "dead", f"Expected dead, got {row['status']}"
    dl = conn.execute("SELECT * FROM dead_letters WHERE event_id=1").fetchone()
    assert dl is not None, "Dead letter not created"
    assert dl["dead_reason"] == "TEST_FAILURE"
    w.conn.close()
    teardown_db()

@test("Dead letter — archive overflow with VACUUM threshold")
def test_deadletter_overflow():
    """archive_overflow should not VACUUM unconditionally (Linus+Guido fix)."""
    w = setup_db()
    result = archive_overflow(w)
    assert "vacuumed" in result
    # Should NOT VACUUM on small data
    assert result["vacuumed"] is False, "VACUUMed unconditionally (should be threshold-based)"
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 9: Observability
# ----------------------------------------------------------------
@test("Observability — metrics record + snapshot")
def test_metrics():
    m = EventBusMetrics()
    m.record_write(1.5)
    m.record_write(2.0)
    m.record_write(3.0)
    m.record_read()
    s = m.snapshot()
    assert s["events_written_total"] == 3
    assert s["events_read_total"] == 1
    assert "write_latency_ms" in s
    assert s["write_latency_ms"]["p50"] == 2.0
    assert s["write_latency_ms"]["p95"] == 3.0
    assert s["write_latency_ms"]["p99"] == 3.0

@test("Observability — health_check on live DB")
def test_health():
    w = setup_db()
    publish_event.publish_event(event_type="test:hc", payload={}, source_agent="tester")
    hc = health_check(TEST_DB)
    assert hc["status"] in ("ok", "warning")
    assert "checks" in hc
    assert hc["checks"].get("wal_mode") == "wal"
    assert "db_size_mb" in hc["checks"]
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 10: Schema version constant
# ----------------------------------------------------------------
@test("Schema — MAX_TTL_SECONDS constant")
def test_ttl_constant():
    assert MAX_TTL_SECONDS == 86400

# ----------------------------------------------------------------
# Test 11: Reader context manager
# ----------------------------------------------------------------
@test("Reader — context manager acquire/release")
def test_reader_cm():
    w = setup_db()
    reader = EventBusReader(TEST_DB)
    with reader.acquire() as conn:
        assert conn is not None
        row = conn.execute("SELECT 1").fetchone()
        assert row[0] == 1
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Test 12: Event validation (publish with invalid type)
# ----------------------------------------------------------------
@test("Publish — invalid event_type rejected")
def test_invalid_event_type():
    w = setup_db()
    try:
        publish_event.publish_event(event_type="INVALID", payload={}, source_agent="tester")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    w.conn.close()
    teardown_db()

# ----------------------------------------------------------------
# Run
# ----------------------------------------------------------------
if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"  Phase 1 v2 — Integration Test Suite")
    print(f"{'='*60}")

    tests = [
        test_schema,
        test_write_read,
        test_cursor,
        test_multi_consumer,
        test_parallel,
        test_wal_checkpoint,
        test_wal_persistent,
        test_nfs_pass,
        test_nfs_exception,
        test_deadletter_migrate,
        test_deadletter_overflow,
        test_metrics,
        test_health,
        test_ttl_constant,
        test_reader_cm,
        test_invalid_event_type,
    ]

    for t in tests:
        t()

    print(f"\n{'='*60}")
    print(f"  Results: {PASS} PASS / {FAIL} FAIL")
    if ERRORS:
        print(f"\n  Failures:")
        for e in ERRORS:
            print(f"    {e}")
    print(f"{'='*60}")

    sys.exit(0 if FAIL == 0 else 1)
