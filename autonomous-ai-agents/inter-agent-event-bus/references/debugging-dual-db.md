# Debugging: Dual DB location issue

## Symptoms

- `subscribe_events()` returns no events even though events were published
- Direct SQL query of `~/.hermes/hermes-agent/skills/.../event_bus.db` shows data,
  but code returns empty
- Only stale test data visible in one DB, live data in another

## Root cause

The event bus has **two** SQLite databases:

| DB | Path | Contains |
|----|------|----------|
| **Shared (live)** | `~/.hermes/shared/event_bus.db` | Runtime events from `publish_event()` |
| **Skill-dir (seed)** | `~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus/event_bus.db` | Test/seed data from test suite |

The code always writes to the **shared** DB. The seed DB is populated
only by test scripts.

## Quick check script

Run this to see both DBs side-by-side:

```python
#!/usr/bin/env python3
"""Compare both event bus databases."""
import sqlite3, os

paths = [
    os.path.expanduser("~/.hermes/shared/event_bus.db"),
    os.path.expanduser("~/.hermes/hermes-agent/skills/"
                       "autonomous-ai-agents/inter-agent-event-bus/event_bus.db"),
]

for db_path in paths:
    label = "SHARED" if "shared" in db_path else "SKILL-DIR"
    exists = os.path.exists(db_path)
    print(f"[{label}] {db_path}")
    print(f"  Exists: {exists}")
    if not exists:
        continue
    print(f"  Size: {os.path.getsize(db_path)} bytes")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r["name"] for r in cur.fetchall()]
    print(f"  Tables: {tables}")
    for tname in tables:
        cur.execute(f'SELECT COUNT(*) as cnt FROM "{tname}"')
        print(f"    {tname}: {cur.fetchone()['cnt']} rows")
        if tname == "events":
            cur.execute(f'SELECT topic, COUNT(*) as c FROM "{tname}" GROUP BY topic')
            for r in cur.fetchall():
                print(f"      topic={r['topic']}: {r['c']}")
    conn.close()
```

## Resolution

Ensure your code imports from the skill's `tools/` directory — that's
the only code path that writes to and reads from the shared DB.
Direct SQL querying of the seed DB is only useful for understanding
the schema or debugging test data.
