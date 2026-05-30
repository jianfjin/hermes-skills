# Edsger W. Dijkstra — Phase 1 v2 Code Review

**Reviewer**: Edsger W. Dijkstra (CSO)
**Date**: 2026-05-29
**Style**: EWD498 — Mathematical Correctness Audit

---

| File | Verdict | Issues | Suggestions |
|------|---------|--------|-------------|
| connection.py | PASS_WITH_RESERVATIONS | Singleton instantiation lacks proven thread-safety. __exit__ exception contract unspecified. | Double-checked locking. Document exception propagation. |
| event_schema_v2.py | PASS | AUTOINCREMENT overhead for append-only log. 86400 magic constant. | Symbolic constant MAX_TTL_SECONDS. Document AUTOINCREMENT necessity. |
| wal_checkpoint.py | **FAIL** | TRUNCATE demands exclusive access. 30s daemon thread ignores WAL concurrency. Magic thresholds. | Switch to PASSIVE checkpointing. Join thread on shutdown. Remove TRUNCATE. |
| nfs_check.py | **FAIL** | sys.exit(1) from library module violates modular composition. Linux-specific. | Raise FilesystemNotSupportedError. Abstract for POSIX compliance. |
| dead_letter.py | PASS_WITH_RESERVATIONS | O(operations) connection overhead per call. TTL semantics confused between events and dead_letters. | Persistent writer connection. Clarify dead letter TTL domain. |
| observability.py | PASS_WITH_RESERVATIONS | Ring buffer thread-safety unproven. O(n log n) percentile sorting. | threading.Lock. Quickselect or bounded histogram. |
| publish_event.py | PASS | — | Ensure Writer connection not mutated by concurrent threads. |
| subscribe_events.py | PASS_WITH_RESERVATIONS | LIKE without covering index = O(n) full scan. Leading wildcards defeat B-tree. | Prefix-only patterns + idx_events_event_type. Atomic cursor+ack. |
| event_bus_status.py | PASS | Thin wrapper. | Add circuit-breaker threshold for consecutive health_check failures. |
| deploy_phase1.sh | PASS_WITH_RESERVATIONS | Shell has no type safety. pip without pinned versions. No rollback. | Pin with requirements.txt hashes. Add rollback hook. |
| migrate_schema_v2.py | PASS | None. | Add CI test for v1→v2→v1 idempotency. |

---

## OVERALL VERDICT: PASS_WITH_RESERVATIONS

"The deletion of ConnectionPool, retry decorators, and application-level _db_lock demonstrates a maturing respect for SQLite's own serializability — an encouraging sign of algorithmic honesty. However, two FAILs (nfs_check.py, wal_checkpoint.py) reveal fundamental misunderstandings of library boundaries and WAL concurrency. A program that sys.exit()s from a library module or checkpoints TRUNCATE blindly from a daemon thread is not reliable; it is merely lucky. Fix the FAILs before Phase 2. Program testing can show the presence of bugs, but is hopelessly inadequate for showing their absence."
