# Phase 1 SQLite WAL Optimization (2026-05-29)

A full Phase 1 implementation plan was developed and reviewed for optimizing the SQLite event bus in <5 agent scenarios. All docs at `~/.hermes/docs/event-bus/`.

## Key Files

| File | Content |
|------|---------|
| `inter-agent-event-bus-Phase1-v2-完整方案-20260529.md` | Final v2 plan (1143 lines, 42KB) — recommended starting point |
| `phase1-review-linus-guido.md` | Linus Torvalds + Guido van Rossum review |
| `inter-agent-event-bus-Phase1-技术方案-张小龙制定-20260529.md` | v1 plan (historical) |
| `event-bus-review-feifei-report.md` | Fei-Fei's validation |
| `event-bus-review-xiaolong-notes.md` | Initial Xiaolong architecture notes |
| `event-bus-review-zhaoxiaolong-rabbitmq-notes.md` | RabbitMQ vs Redis analysis |

## v2 vs v1 Key Changes (17 total)

Per review from Linus Torvalds and Guido van Rossum:

| # | Change | Type | Rationale |
|:-:|--------|:----:|-----------|
| 1 | Remove mmap_size=256MB | DELETE | OOM risk; append-only access pattern doesn't benefit |
| 2 | 500ms polling → sqlite3_update_hook + inotify | DELETE+ADD | Linus: "500ms polling = slower than shell script" |
| 3 | ConnectionPool → 1 Writer + N Reader | DELETE | Guido: "ConnectionPool in single-process worker is ceremony" |
| 4 | Remove failover election | DELETE | Single machine: restart on crash, not consensus |
| 5 | Remove Single Writer Agent | DELETE | WAL mode supports concurrent reads natively |
| 6 | Remove @retry_on_busy decorator | DELETE | Redundant with PRAGMA busy_timeout=5000 |
| 7 | Add Event Schema (events + consumer_cursors + dead_letters) | ADD | Linus: "biggest architectural smell — undefined event model" |
| 8 | Add Cursor-based incremental reads | ADD | Consumer position tracking |
| 9 | Add WAL Checkpoint timer (30s TRUNCATE) | ADD | Prevents unbounded WAL growth (GB-scale事故) |
| 10 | Add NFS startup check | ADD | SQLite + NFS = silent corruption |
| 11 | Add Dead letter + overflow archive | ADD | 3 conditions for dead-lettering |
| 12 | Add Schema migration strategy | ADD | SCHEMA_VERSION table + idempotent migrations |
| 13 | Add Observability (3 layers) | ADD | JSON logging + P50/P95/P99 + HTTP health |
| 14 | Add context manager protocol | ADD | Guido: `with reader.acquire() as conn:` required |
| 15 | Hardware-specific benchmarks | MOD | AMD EPYC 7713 + NVMe, microsecond targets |
| 16 | 9 manual steps → deploy_phase1.sh | MOD | One-command deployment |
| 17 | 7-day timeline reorganized | MOD | New structure from Day1-Day7 |

## Linus Torvalds Review Highlights

### What he called "not stupid"
- journal_mode=WAL, synchronous=NORMAL, foreign_keys=ON — baseline common sense
- busy_timeout=5000 with retry decorator — both isn't wrong
- Single writer intuition — SQLite is single-writer

### What he called "stupid and/or cargo cult"
- mmap_size=256MB — "copy-pasted from a Medium article"
- polling 500ms — "slower than a shell script checking a file. Random jitter is cosmetic"
- ConnectionPool — "pointless ceremony. Adding failure modes to solve a non-problem"
- Failover — "from naive to fantasy. Distributed consensus for a single-machine system"

### Production killers ranked by probability
1. WAL checkpoint starvation → unbounded WAL growth → disk full → everything dies
2. SQLITE_BUSY thundering herd under real concurrency
3. Split-brain in failover → silent data inconsistency
4. 9-step manual deployment → someone runs them out of order

### Bottom line
"Prototype plan dressed up with performance metrics and deployment steps to look complete. Biggest architectural smell: you designed an event bus without specifying the EVENT MODEL."

## Guido van Rossum Review Highlights

### Three raincoats problem
busy_timeout (C layer) + manual Python retry + @retry_on_busy decorator = triple redundancy. Pick one.

### Missing context manager
"ConnectionPool without `with pool.acquire() as conn:` is simply not done in Python."

### Single Writer Agent
"Biggest red flag. WAL mode exists precisely so you don't need a designated writer."

## 7-Day Timeline (from v2)

| Day | Focus |
|:---:|-------|
| 1 | Event Schema v2 + Reader/Writer connections + context manager + NFS check + WAL Checkpoint |
| 2 | sqlite3_update_hook listener + inotify WAL directory + cursor reads + dead letters |
| 3 | Observability: JSON logging + P50/P95/P99 + HTTP health endpoint |
| 4 | deploy_phase1.sh + migrate_schema_v2.py + rollback verification |
| 5 | Hardware-specific benchmark on AMD EPYC 7713 + NVMe |
| 6 | Integration + stress: 5-agent concurrent write, kill-process test, WAL pressure, dead letter overflow, NFS rejection |
| 7 | Retrospective + Phase 2 planning |
