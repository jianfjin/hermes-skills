# Event Bus Daemon Architecture

## Architecture History

The Event Bus started as a purely passive SQLite store — agents called `publish_event` and `subscribe_events` directly. Three architectures were considered for automated event delivery:

**Attempt 1: Polling daemon** (rejected)
A standalone process that runs `SELECT * FROM events WHERE id > :cursor` in a loop, matches topics against a routing table, and spawns profile agents via `delegate_task`.

- Rejected because the existing `hooks/` subsystem (inside `publish_event.py`) already provides delivery callbacks, circuit breakers, retry, and DLQ.
- Writing a second delivery path duplicates all of this.

**Attempt 2: Pure hooks callback daemon** (implementation path A)
A lightweight daemon that only registers a wildcard callback with the hooks subsystem and does nothing else — the hooks subsystem drives all delivery.

- Clean, event-driven, no polling.
- But: the daemon has no control over delivery ordering; hooks fires callbacks synchronously inside `publish_event()`.

**Attempt 3: Polling + callback (AVOID — validated bug)**
Both registers a wildcard callback AND runs a polling loop. Each event gets processed twice.

- This was the actual first implementation. Detected by Karpathy during code review as a CRITICAL defect.
- The fix: choose one path. Pure callback (path A) is recommended for simplicity.

## Recommended Architecture

```
publish_event() ──> SQLite ──> hooks.deliver_event()
                                   │
                           CallbackRegistry
                                   │
                           route_callback()
                                   │
                           spawn_profile_agent()
                                   │
                           delegate_task()
```

The daemon process:
1. Calls `hooks.register_callback("*", route_callback)` to subscribe to ALL events
2. Calls `_stop_event.wait()` to stay alive for signal handling
3. Handles SIGTERM (graceful shutdown), SIGHUP (route config reload)
4. Sends `sd_notify("READY=1")` for systemd integration
5. Writes periodic heartbeats (`daemon-2b.alive`) for liveness probes

## Key Implementation Decisions

### Use Hooks Callbacks, Not Polling

```python
# CORRECT: register a callback and let hooks drive delivery
hooks = setup_delivery_hooks(db_path=db_path)
hooks.register_callback("*", lambda eid, t, p, m: route_callback(eid, t, p, m))

# WRONG: DON'T also poll the DB
# for event in get_pending_events(): hooks.deliver_event(event)  # DUAL DELIVERY
```

### Enable WAL Mode on All SQLite Connections

Without WAL mode, concurrent writes from ThreadPoolExecutor workers produce `sqlite3.OperationalError: database is locked`.

```python
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")
```

### Unify Database Path Across Modules

All modules (daemon, DLQ, health) must use the same database path. The daemon should accept `--db-path` and pass it to all sub-modules:

```python
class DeadLetterQueue:
    def __init__(self, db_path: str | None = None, max_failures: int = 3):
        self.db_path = db_path or DEFAULT_DB_PATH

# In daemon main:
dlq = DeadLetterQueue(db_path=args.db_path)
```

## Common Pitfalls

### Dual Delivery Path (CRITICAL)

This is the single most common bug when building on top of the hooks subsystem. The hooks subsystem already fires callbacks synchronously inside `publish_event()`. If you ALSO poll the DB for new events and call `hooks.deliver_event()` on them, every event is delivered twice — once by the hooks subsystem itself, once by your polling loop.

**Detection:** Add logging in `route_callback`. If the same `event_id` appears twice within milliseconds, you have dual delivery.

**Fix:** Delete the polling loop. The callback is the delivery mechanism.

### SQLite Database Locked Under Concurrent Writes

`ThreadPoolExecutor` spawns multiple worker threads that all write to the same SQLite DB (DLQ, failure logging, heartbeat). Without WAL mode, these writes contend on a single database-level lock.

**Symptom:** `sqlite3.OperationalError: database is locked` under load.

**Fix:** `conn.execute("PRAGMA journal_mode=WAL")` on EVERY connection.

### DB Path Inconsistency

When a daemon accepts `--db-path`, every subsystem (DLQ, health check, schema migration) must use the SAME path. The most common bug is hardcoding the path in one module while using `--db-path` in another.

**Symptom:** DLQ tables created in database A, events in database B, they never interact. Dead events are never detected.

**Fix:** Pass `db_path` as a constructor argument to every subsystem.

### Hook Init Failure Should Not Kill the Process

```python
try:
    hooks = setup_delivery_hooks(db_path=db_path)
except ImportError as e:
    logger.warning("hooks subsystem unavailable: %s", e)
    hooks = FallbackHooks(db_path=db_path)  # logs events instead
```

If hooks initialization fails (e.g., skill not installed, path wrong), the daemon should fall back to a logger — not call `sys.exit(1)`. The daemon can still serve systemd watchdog, health checks, and heartbeat.

### Filename Hyphens Break Python Import

`daemon-2b-dlq.py` cannot be imported as `import daemon-2b-dlq` because `-` is not valid in Python identifiers. Either:
- Use underscores: `daemon_2b_dlq.py` (recommended)
- Or use `importlib.import_module("daemon-2b-dlq")` (workaround, not recommended)

## File Organization (Validated Layout)

```
~/.hermes/scripts/
├── daemon_2b.py              # Main daemon (Daemon class, hooks callback, routing, spawn)
├── daemon_2b_dlq.py          # DeadLetterQueue + failure_log
├── daemon_2b_retry.py        # RetryPolicy (exp backoff + full jitter)
├── daemon_2b_health.py       # Heartbeat + sd_notify + liveness
├── daemon_2b_schema.py       # SubagentResult TypedDict

~/.hermes/config/
├── daemon-2b-routes.yaml     # topic → profile routing table
├── daemon-2b-config.yaml     # daemon config (pool size, timeouts)
├── daemon-2b.service         # systemd unit (Type=notify, WatchdogSec=90)

~/.hermes/tests/
├── test_daemon_2b.py              # Unit tests (31 tests)
├── test_daemon_2b_integration.py  # Integration tests (14 tests)

~/.hermes/run/
├── daemon-2b.alive           # Heartbeat timestamp (written every 30s)
├── daemon-2b.pid             # PID file
```

## Three-Phase Graceful Shutdown

```
Phase 1 (t=0):    Stop accepting new events. Set _stop_event.
Phase 2 (t=1-25): Drain inflight. Wait for _inflight set to empty.
Phase 3 (t=25-30): Force kill executor. shutdown(wait=False, cancel_futures=True).
```

Implemented as a background daemon thread (NOT daemon=True — non-daemon to prevent premature termination).

## References

- `daemon_2b.py` in `~/.hermes/scripts/` — full reference implementation
- `daemon-2b-formal-notes.txt` in `~/.hermes/docs/` — Dijkstra's formal proofs
