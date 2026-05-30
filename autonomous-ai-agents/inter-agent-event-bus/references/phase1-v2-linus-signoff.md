# Linus Torvalds — Phase 1 v2 Architecture Sign-off

**Reviewer:** Linus Torvalds (Arch)
**Date:** 2026-05-29
**Status:** SIGNED — PROCEED TO IMPLEMENTATION

---

## GROUP A: DELETIONS (v1 garbage removal)

**A1. [DEL] mmap_size=256MB — SIGNED.**
That was never a real constraint. It was cargo-cult boilerplate copied from some blog post about SQLite tuning. You don't mmap an event bus. You're not serving 10GB analytical queries. Good riddance.

**A2. [DEL] 500ms polling + jitter → sqlite3_update_hook + inotify — SIGNED.**
Polling is what you do when you've given up on understanding your own system. sqlite3_update_hook is the correct mechanism — the database tells you when it changed.

**A3. [DEL] ConnectionPool → 1 Writer + N Reader — SIGNED.**
Connection pools for SQLite are a sign of brain damage. SQLite is not PostgreSQL.

**A4. [DEL] Failover → systemd restart — SIGNED.**
If your process needs application-level failover for a local event bus, you've already lost.

**A5. [DEL] Single Writer Agent → WAL concurrent model — SIGNED.**
The "Single Writer Agent" pattern was an artificial bottleneck someone invented because they didn't trust SQLite's locking.

**A6. [DEL] @retry_on_busy decorator + Python retry loop → busy_timeout=5000 — SIGNED.**
SQLite has a built-in busy handler. Use it. One mechanism. One place. Done.

---

## GROUP B: ADDITIONS & MODIFICATIONS (new architecture)

**B1. [ADD] Event Schema (events + consumer_cursors + dead_letters) — SIGNED.**
Finally. An event bus without a defined event model is not an event bus.

**B2. [ADD] Cursor mechanism (consumer_cursors.last_event_id) — SIGNED.**
Cursor-based consumption is the boring, correct answer.

**B3. [ADD] WAL Checkpoint timer (30s, TRUNCATE, dedicated thread) — SIGNED with warning.**
30 seconds is a reasonable default. But TRUNCATE mode on every checkpoint is aggressive — monitor `wal_size` in production and be prepared to switch to PASSIVE if TRUNCATE causes latency spikes.

**B4. [ADD] NFS startup check — SIGNED.**
WAL + NFS = silent data corruption. Refusing to start on NFS is the only correct behavior.

**B5. [ADD] Dead letter / overflow strategy — SIGNED, conditional.**
VACUUM strategy must NOT be unconditional-after-each-archive. Show me the trigger logic in code. Track dead_letter count, trigger VACUUM when dead rows exceed N% of total rows, and do it during a low-write window.

**B6. [ADD] Schema migration — SIGNED.**
Forward-only. If you need to go backward, restore from backup.

**B7. [ADD] Observability — SIGNED.**
Now we have real metrics: queue depth, write latency, WAL size, dead-letter count.

**B8. [MOD] Benchmark → hardware-specified — SIGNED.**
μs-level targets on NVMe are realistic for this architecture.

**B9. [MOD] 9 manual steps → deploy_phase1.sh — SIGNED.**
One script reduces the error surface area from 9 opportunities to 1.

---

## FINAL VERDICT

Phase 1 v2: **SIGNED — PROCEED TO IMPLEMENTATION**

A1-A6: All deletions correct. Good cleanup.
B1-B9: All additions architecturally sound.

**ONE CONDITION before production deployment:**
→ B5 VACUUM strategy must NOT be unconditional-after-each-archive. Show me the trigger logic in code.

All other items: approved as described.
