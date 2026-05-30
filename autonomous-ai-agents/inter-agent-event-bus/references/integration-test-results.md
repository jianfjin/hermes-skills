# Phase 1 v2 Integration Test Results (2026-05-29)

## Test Suite

**File:** `tests/test_phase1_v2_integration.py` — 16 scenarios, 5-agent parallel throughput

## Results

```
  Schema creation + migration              PASS
  Writer singleton + publish+subscribe      PASS
  Cursor — incremental reads                PASS
  Multiple consumers — independent cursors  PASS
  5-agent parallel writes — 0 SQLITE_BUSY   PASS  (1,000 events)
  WAL checkpoint — task lifecycle           PASS
  WAL checkpoint — persistent across writes PASS
  NFS check — local FS passes               PASS
  NFS check — FilesystemNotSupportedError   PASS
  Dead letter — migrate single event        PASS
  Dead letter — archive overflow+VACUUM     PASS
  Observability — metrics + snapshot        PASS
  Observability — health_check on live DB   PASS
  Schema — MAX_TTL_SECONDS constant         PASS
  Reader — context manager acquire/release  PASS
  Publish — invalid event_type rejected     PASS
────────────────────────────────────────────────
  Results: 16 PASS / 0 FAIL
```

## E2E Test

**File:** `tests/test_phase1_v2_e2e.py` — 33 scenarios simulating 3-agent workflow

### Scenarios
1. feifei publishes 10 gradient events → xuefeng subscribes (cursor works)
2. Independent consumer (zhangsan) reads all 13 feifei events
3. Multi-type events with wildcard (`*`, `agent:*`, exact match)
4. NFS check on local FS
5. Health check with live data
6. WAL checkpoint under load (20 events)
7. Dead letter simulation
8. Metrics observability

```
  Results: 33 PASS / 0 FAIL
```

## Runtime Bugs Discovered

| Bug | Symptom | Fix |
|-----|---------|-----|
| Missing `import sqlite3` in `publish_event.py` | `NameError: name 'sqlite3' is not defined` | Added import |
| No `row_factory` on writer connection | `TypeError: tuple indices must be integers, not str` on `row["created_at"]` | Added `conn.row_factory = sqlite3.Row` |
| No `check_same_thread=False` | `ProgrammingError: SQLite objects created in a thread...` | Added parameter to `sqlite3.connect()` |
| Multi-statement SQL via single `execute()` | "You can only execute one statement at a time" | Split into separate `execute()` calls |
| Thread-unsafe writer singleton | `cannot commit - no transaction is active` in parallel write | Added `write_lock = threading.Lock()` |
| Reader singleton cached across test runs | Cursor tests found 0 events | Reset `subscribe_events._reader = None` in test teardown |
| Writer singleton cached across test runs | State leaks between tests | Reset `EventBusWriter._instance = None` |
