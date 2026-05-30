# Hermes Inter-Agent Event Bus — Final Proposal v2

**Author:** Andrej Karpathy (CRO)
**Reviews:** Fei-Fei Li (CAS), Linus Torvalds (Arch), Edsger Dijkstra (CSO), Guido van Rossum (CLA), Zhang Xiaolong (Eng) + Demi Guo (CCT)
**Status:** ✅ CONDITIONAL_APPROVE — see tasks for fix list
**Date:** 2026-05-29

---

## Architecture Decision: A Hermes Skill, Not Core

Skill: `inter-agent-event-bus` under `autonomous-ai-agents` category.

**Why skill, not core:**
1. Role alternation preserved (events injected as synthetic tool results, not assistant messages)
2. Zero risk to prompt cache
3. Optional — agents degrade gracefully without the bus
4. Ships independently — no core Hermes release dependency
5. Matches existing Kanban pattern

---

## Corrected Schema (Fei-Fei's fix)

```sql
CREATE TABLE events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT UNIQUE NOT NULL,
    topic       TEXT NOT NULL,
    publisher   TEXT NOT NULL,
    payload     TEXT NOT NULL,
    ttl         INTEGER NOT NULL DEFAULT 86400,  -- Fei-Fei: 24h not 1h
    created_at  REAL NOT NULL DEFAULT (julianday('now'))
);
CREATE INDEX idx_events_topic ON events(topic);
CREATE INDEX idx_events_created ON events(created_at);

CREATE TABLE cursors (
    agent_id       TEXT NOT NULL,
    topic_pattern  TEXT NOT NULL,           -- Fei-Fei: composite PK
    last_event_id  INTEGER NOT NULL DEFAULT 0,
    updated_at     REAL NOT NULL DEFAULT (julianday('now')),
    PRIMARY KEY (agent_id, topic_pattern)  -- FIXED: not single-agent key
);
```

---

## Corrected Interface (Guido's review)

```python
def publish_event(
    topic: str,              # validated: ^[a-z][a-z0-9_-]+:[a-z][a-z0-9_-]+$
    payload: dict,           # JSON-serializable
    ttl_seconds: int = 86400 # Fei-Fei: 24h default
) -> dict:
    """
    Returns {event_id, topic, timestamp, status}.
    """
    # Error handling (Linus): try/except for SQLITE_BUSY, JSON encode failure
    # Connection mgmt (Linus): check_same_thread=False + mutex
    # TTL cleanup (Fei-Fei): sampling check then DELETE
    # WAL mode (Fei-Fei): 2 lines at connection init
```

```python
def subscribe_events(
    topic_pattern: str,      # exact or wildcard: "feifei:*"
    since_event_id: int = 0, # uses auto-increment INTEGER, not uuid4
    max_events: int = 10,
    block_seconds: int = 0   # polling approximation (Fei-Fei), not true blocking
) -> list[dict]:
    """
    Returns {event_id, topic, payload, timestamp, publisher}.
    Each (agent, topic_pattern) pair maintains independent cursor.
    """
```

---

## Code Structure (Linus's corrected estimate)

| File | Lines | Notes |
|------|-------|-------|
| SKILL.md | ~50 | Metadata, instructions |
| tools/publish_event.py | ~120 | +error handling, validation, docstring (Linus) |
| tools/subscribe_events.py | ~130 | +cursor mgmt, pattern matching, blocking |
| tools/event_cleanup.py | ~45 | +sampling optimization |
| tools/event_bus_status.py | ~40 | New — Fei-Fei's observability tool |
| connection.py | ~30 | New — connection manager (Linus: check_same_thread) |
| schema.sql | ~30 | DDL + indexes |
| references/architecture.md | ~80 | Usage guide + scaling ceiling doc |
| hooks/delivery.py | ~60 | New — delivery callback registry (Xiaolong's gap) |
| **Total** | **~485** | Linus: 350 is optimistic, real number |

---

## All Review Findings Incorporated

| # | Finding | From | Severity | Fix |
|---|---------|------|----------|-----|
| 1 | Cursor composite PK | Fei-Fei | 🔴 BLOCKER | agent_id + topic_pattern |
| 2 | Delivery hooks missing | Xiaolong | 🔴 BLOCKER | Add callback registry |
| 3 | `since_event_id` ambig | Linus | 🟡 CRITICAL | Use auto-increment, drop uuid4 or document |
| 4 | Connection mgmt missing | Linus | 🟡 CRITICAL | check_same_thread + mutex |
| 5 | Zero error handling | Linus | 🟡 CRITICAL | try/except in all tools |
| 6 | Delivery guarantee contradiction | Linus | 🟢 WARNING | Own at-least-once or drop cursors |
| 7 | TTL default 3600→86400 | Fei-Fei | 🟢 WARNING | Changed |
| 8 | WAL mode + busy_timeout | Fei-Fei | 🟢 WARNING | 2 lines at connection init |
| 9 | Observability tool missing | Fei-Fei | 🟢 WARNING | Add event_bus_status (~40 lines) |
| 10 | Topic validation missing | Fei-Fei | 🟢 WARNING | Add regex validation |
| 11 | Line count optimistic | Linus | 🟢 WARNING | ~350 → ~485 |
| 12 | Skill name redundant | Fei-Fei | 🟢 WARNING | agent-event-bus → inter-agent-event-bus |
| 13 | Return value missing topic | Fei-Fei | 🟢 WARNING | Add topic to return value |
| 14 | `block_seconds` not blocking | Fei-Fei | 🟢 WARNING | Document: polling approximation |
| 15 | Formal: not a bus, poll queue | Dijkstra | ℹ️ NOTE | Correct but trivial. Name honestly. |

---

## Implementation Tasks

### P0 — Pre-ship Blockers (must fix before Phase 1)

- [ ] Fix cursor table to composite PRIMARY KEY (agent_id, topic_pattern)
- [ ] Add delivery hook callback registry (Xiaolong to implement — 29 years experience)
- [ ] Clarify since_event_id type: auto-increment INTEGER, drop uuid4

### P1 — Phase 1 (Safety + Correctness)

- [ ] Add connection manager: check_same_thread=False + threading.Lock()
- [ ] Add error handling to publish_event: try/except SQLITE_BUSY, JSON failure
- [ ] Add error handling to subscribe_events: pattern matching, cursor upsert
- [ ] Set PRAGMA journal_mode=WAL and PRAGMA busy_timeout=5000 at connection init
- [ ] Add topic validation regex: ^[a-z][a-z0-9_-]+:[a-z][a-z0-9_-]+$
- [ ] Change TTL default: 3600 → 86400
- [ ] Add topic to publish_event return dict
- [ ] Document block_seconds as polling approximation, not true blocking

### P2 — Phase 2 (Observability + Polish)

- [ ] Implement event_bus_status tool (~40 lines, Fei-Fei's spec)
- [ ] Implement TTL cleanup with sampling check (Fei-Fei's optimization)
- [ ] Document at-least-once delivery semantics (Linus: own it or drop it)
- [ ] Update line count estimate: ~350 → ~485 (Linus's audit)
- [ ] Rename skill: agent-event-bus → inter-agent-event-bus (Fei-Fei)
- [ ] Document scaling ceiling: designed for sub-100K events (Fei-Fei)

### P3 — Phase 3 (Integration)

- [ ] Webhook bridge: events trigger webhook delivery
- [ ] Cron-driven consumers: example cron jobs
- [ ] Memory integration: auto-inject on next session start
- [ ] Architecture reference doc with usage guide

### P4 — Future

- [ ] Replace SQLite backend with Redis/NATS for multi-user deployments
- [ ] Event schema versioning convention
- [ ] Source-of-truth tagging (fact vs opinion vs interim result — Fei-Fei's ImageNet lesson)

---

## Ownership

| Component | Owner | Rationale |
|-----------|-------|-----------|
| Delivery hooks | **Zhang Xiaolong** | Foxmail → QQ Mail → WeChat → Hermes. 29 years. |
| publish_event tool | Karpathy | Original author |
| subscribe_events tool | Fei-Fei | Found the cursor bug, knows the fix |
| event_bus_status tool | Fei-Fei | Her spec |
| Connection manager | Linus audit | His review finding |
| Schema + WAL | Guido review | His Pythonic standards |
| Architecture ref doc | All | Collective |

---

## Final Verdict

**6 reviews. 15 findings. 2 blockers. 2 critical. 9 warnings. 1 note.**

Proceed with implementation. Fix P0 before Phase 1 ships. P1 + P2 in first sprint. P3 + P4 as demand grows.

*— Consolidated by 峨眉峰, 2026-05-29*
