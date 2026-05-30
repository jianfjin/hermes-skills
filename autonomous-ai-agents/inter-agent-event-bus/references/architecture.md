# Architecture Reference

> **See also:** DESIGN.md · SKILL.md · hooks/ · tools/

## Overview

The Inter-Agent Event Bus is a lightweight pub/sub system built as a
Hermes skill.  It uses SQLite as its backing store (single file, zero
daemon), delivers events in-process via registered callbacks (delivery
hooks), and supports external polling via `subscribe_events`.

**Design philosophy:** simple, optional, no infrastructure.  Agents that
load the skill get event passing.  Agents that don't, don't.  No core
Hermes component depends on it.

## Schema

### Core Tables

```sql
CREATE TABLE events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      TEXT    NOT NULL UNIQUE,      -- UUID4 string
    topic         TEXT    NOT NULL,
    schema_version TEXT   NOT NULL DEFAULT '1.0',
    payload       TEXT    NOT NULL,              -- JSON
    ttl_seconds   INTEGER NOT NULL DEFAULT 86400,
    created_at    REAL    NOT NULL,              -- unix timestamp
    expires_at    REAL    NOT NULL               -- created_at + ttl_seconds
);
CREATE INDEX idx_events_topic   ON events(topic);
CREATE INDEX idx_events_created ON events(created_at);

CREATE TABLE cursors (
    agent_id       TEXT NOT NULL,
    topic_pattern  TEXT NOT NULL,                -- composite PK
    last_event_id  INTEGER NOT NULL DEFAULT 0,  -- references events.id
    updated_at     REAL NOT NULL,
    PRIMARY KEY (agent_id, topic_pattern)
);
```

**Design rationale (Fei-Fei's fix):** The `cursors` table uses a composite
primary key `(agent_id, topic_pattern)` — not a single-column agent_id key.
This means each (agent, subscription) pair maintains an independent
cursor, enabling:

- Multiple agents consuming the same topic at different speeds
- Multiple subscriptions per agent with independent progress tracking
- Subscriber-safe replay: reset cursor to 0 to re-consume

### Dead Letter Queue

```sql
CREATE TABLE dead_letter_queue (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT NOT NULL,
    topic           TEXT NOT NULL,
    payload         TEXT NOT NULL,               -- JSON
    callback_id     TEXT NOT NULL,
    callback_meta   TEXT DEFAULT '{}',           -- JSON
    failure_reason  TEXT,
    attempts        INTEGER NOT NULL,
    total_time_ms   REAL,
    created_at      REAL NOT NULL DEFAULT (julianday('now'))
);
```

## Tool API Specs

### publish_event

```
INPUT:
    topic:         str   — Required. Regex: ^[a-z][a-z0-9_-]+:[a-z][a-z0-9_-]+$
    payload:       any   — JSON-serializable (default {})
    schema_version: str  — Semantic version tag (default "1.0")
    ttl_seconds:   int   — TTL in seconds (default 86400 = 24 h)

OUTPUT: dict
    {
        "event_id":  "<uuid4>",
        "topic":     "<topic>",
        "timestamp": <unix_float>,
        "status":    "published"
    }

RAISES:
    ValueError        — malformed topic
    TypeError         — payload not JSON-serializable
    sqlite3.OperationalError — DB busy after 5 s timeout

BEHAVIOR:
    1. Validate topic regex
    2. Serialize payload to JSON
    3. Generate UUID4 event_id
    4. INSERT into events table (thread-safe via mutex)
    5. Best-effort sample cleanup: DELETE up to 50 expired rows
    6. Fire delivery hooks (in-process callback dispatch)
```

### subscribe_events

```
INPUT:
    topic_pattern:  str   — Required. Exact topic or wildcard (e.g. "feifei:*", "*")
    agent_id:       str   — Consumer identity (default "default")
    since_event_id: int   — Override cursor start (default 0 → use stored cursor)
    max_events:     int   — Max results (1-100, default 10)
    block_seconds:  int   — Poll wait time in s, 100 ms interval (default 0)

OUTPUT: list[dict]
    [{
        "event_id":  <int>,         -- auto-increment id, NOT uuid4
        "topic":     "<topic>",
        "payload":   "<json_str>",  -- raw JSON string from DB
        "timestamp": <unix_float>,
        "publisher": "<publisher>"
    }, ...]

BEHAVIOR:
    1. Validate topic_pattern (length 1-256, regex match)
    2. Look up stored cursor for (agent_id, topic_pattern) if since_event_id=0
    3. Convert wildcard to SQL LIKE: "feifei:*" → "feifei:%"
    4. Poll loop: query events WHERE id > cursor AND topic LIKE pattern
       — returns immediately if events found
       — otherwise sleep 100 ms and retry, up to block_seconds deadline
    5. Advance cursor: UPSERT last_event_id = max returned id
    6. Return results list (possibly empty)
```

### event_bus_status

```
INPUT: (none)

OUTPUT: dict
    {
        "total_events":             <int>,
        "oldest_unexpired_age_sec": <float>,
        "active_cursors":           <int>,
        "topic_histogram":          {"topic_A": count, ...},
        "db_path":                  "<path>"
    }

BEHAVIOR:
    - SELECT COUNT(*) FROM events
    - Find oldest event where expires_at > now, compute age in seconds
    - SELECT COUNT(*) FROM cursors
    - GROUP BY topic + COUNT(*) for histogram
    - Returns partial data on DB errors (logs warning, sets _error key)
```

## Event Flow

```
                        ┌──────────────────────────────────────┐
                        │          Agent Process Space          │
                        │                                        │
  ┌──────────┐          │  ┌──────────┐     ┌──────────┐        │
  │ Agent A  │──────────┼─▶│publish   │     │ Callback │        │
  │(publisher)│          │  │_event()  │────▶│Registry  │        │
  └──────────┘          │  └────┬─────┘     └────┬─────┘        │
                        │       │                │               │
                        │  ┌────▼─────┐    ┌─────▼──────┐       │
                        │  │ SQLite   │    │ Delivery   │       │
                        │  │ events   │    │ Executor   │       │
                        │  │ table    │    │ (per cb    │       │
                        │  └──────────┘    │  thread)   │       │
                        │                  │            │       │
                        │            ┌─────┴──────┐     │       │
                        │            │ Circuit    │     │       │
                        │            │ Breaker    │─────┼──▶ cb1│
                        │            │ (guard)    │     │       │
                        │            ├────────────┤     │       │
                        │            │ Retry      │─────┼──▶ cb2│
                        │            │ Policy     │     │       │
                        │            ├────────────┤     │       │
                        │            │ Dead       │     │       │
                        │            │ Letter Q   │─────┘       │
                        │            └────────────┘             │
                        │                                        │
                        │  ┌──────────┐     ┌──────────┐        │
  ┌──────────┐          │  │subscribe │     │ Cursors  │        │
  │ Agent B  │◀─────────┼──│_events()  │◀───│ table    │        │
  │(consumer)│          │  └──────────┘     └──────────┘        │
  └──────────┘          │                                        │
                        └──────────────────────────────────────┘
```

## Delivery Semantics: At-Least-Once

The event bus provides **at-least-once** delivery for external consumers
using `subscribe_events`:

1. Consumer calls `subscribe_events()` with a topic pattern
2. Cursor advances to `results[-1].event_id` only after successful read
3. If consumer crashes between read and processing, the cursor is NOT
   advanced — same events are re-delivered on next poll

Acknowledged trade-off (Linus's finding #6): This is a property of the
cursor model.  To upgrade to exactly-once, consumers must acknowledge
explicitly (out of scope for v1).

**For in-process delivery hooks:** At-least-once applies per callback:
retry policy + dead letter queue ensures delivery is attempted at least
`max_retries + 1` times before being abandoned to DLQ.

## Ordered Consumption Helper

Events are consumed in insertion order (ASC by `events.id`, the auto-increment
primary key).  Since SQLite auto-increment guarantees monotonically increasing
IDs (within a connection), all consumers see events in publish order.

To enforce strict per-partition ordering, filter by topic and ORDER BY id:

```python
results = conn.execute(
    "SELECT * FROM events WHERE topic = ? AND id > ? ORDER BY id ASC",
    (topic, cursor)
).fetchall()
```

This guarantees FIFO within a single topic.

## Partition Key / FIFO Upgrade Path

The current schema supports a **topic-as-partition-key** model.  For strict
FIFO within a logical partition, the roadmap is:

1. Add an explicit `partition_key` column to `events` (defaults to topic)
2. Add a `partition_cursors` table:
   ```sql
   CREATE TABLE partition_cursors (
       agent_id      TEXT NOT NULL,
       partition_key TEXT NOT NULL,
       last_seq      INTEGER NOT NULL DEFAULT 0,
       PRIMARY KEY (agent_id, partition_key)
   );
   ```
3. Consumers read per-partition: `WHERE partition_key = ? AND id > ?`
4. This provides **strict FIFO per partition** while allowing parallel
   consumption across partitions

This is a P4 upgrade — not implemented in v1.

## Scaling Ceiling

Designed for **sub-100K active events** (Fei-Fei's validated ceiling).

| Dimension | Limit | Constraint |
|-----------|-------|------------|
| Active events | ~100,000 | SQLite B-tree page cache, WAL overhead |
| Event throughput | ~1,000/s | SQLite write lock contention |
| Concurrent subscribers | ~50 | Thread-per-callback model |
| Event payload | ~256 KB | Single SQLite row limit (practical) |
| DB size | ~1 GB | WAL file growth + VACUUM overhead |
| Subscription latency | ~100 ms | Polling interval floor |

**Beyond 100K events:** Deploy Redis, NATS, or Kafka as the backing
transport.  The tool API surface (publish_event / subscribe_events /
event_bus_status) can be reimplemented against a different backend
without changing agent code.

## References

- DESIGN.md — Original proposal with all review findings
- SKILL.md — User-facing documentation and quick reference
- tools/publish_event.py — Publish implementation (201 lines)
- tools/subscribe_events.py — Subscribe implementation (136 lines)
- tools/event_bus_status.py — Status observability (62 lines)
- hooks/hooks.py — DeliveryHooks manager, setup_delivery_hooks()
- hooks/registry.py — CallbackRegistry with wildcard matching
- hooks/breaker.py — CircuitBreaker (3-state, thread-safe)
- hooks/retry.py — RetryPolicy (exponential backoff + jitter)
- hooks/executor.py — DeliveryExecutor (per-callback threads)
- hooks/dlq.py — DeadLetterQueue (SQLite-backed)
- hooks/persistence.py — SnapshotManager (JSON snapshots)
