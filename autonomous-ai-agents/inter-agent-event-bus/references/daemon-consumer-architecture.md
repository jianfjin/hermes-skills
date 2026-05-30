# Daemon + Cron Consumer Architecture

## The Problem

Daemon 2b originally spawned profile agents via `hermes -z "goal" --profile feifei` (subprocess). Each spawn:
- Starts a full Hermes agent session (model warmup 8-10s)
- Loads profile SOUL.md + memories
- Processes the goal through the model
- Generates a response

**Total time per event: 2+ minutes.** Three retries = 6+ minutes. Event-driven architecture requires sub-second routing.

## The Solution: Two-Layer Architecture

```
publish_event → Event Bus (SQLite)
  → daemon (hooks callback, ~10ms)
    → INSERT INTO pending_tasks (status='pending')
      → cron job (every 3m, in profile's Hermes session)
        → delegate_task (native tool in session)
        → UPDATE status='completed'
```

### Layer 1: Daemon (Real-Time, Sub-Second)

- Listens on Event Bus via hooks callback
- Routes topic → profile via YAML config
- Writes event to `pending_tasks` table (pure INSERT, ~10ms)
- Returns True immediately (no blocking)

### Layer 2: Cron Consumer (Async, Seconds-to-Minutes)

- Per-profile cron job (`every 3m`) running in a Hermes session
- Reads `pending_tasks WHERE profile='X' AND status='pending' LIMIT 1`
- Claims task: `UPDATE status='processing'`
- Processes via `delegate_task` — natively available in the session
- Completes: `UPDATE status='completed'`

## Why This Works

| Aspect | Daemon (Layer 1) | Cron Consumer (Layer 2) |
|--------|-------------------|------------------------|
| Startup cost | None (already running) | None (cron session is already a Hermes session) |
| Model loading | Not needed | Already loaded in session |
| delegate_task | Not available in standalone Python | ✅ Native tool in session |
| Routing | Real-time (sub-second) | N/A |
| Processing | N/A | Async (seconds-to-minutes) |

## Cron Job Template

Created via `cronjob(action='create', ...)` with these parameters:
- `name`: `<profile>-pending-consumer`
- `schedule`: `every 3m`
- `skills`: `['inter-agent-event-bus']`
- `deliver`: `local`

The prompt should:
1. Identify as the profile's persona
2. Poll `pending_tasks` for status='pending' tasks
3. Claim, process via delegate_task, and mark complete
4. Process only ONE task per run, then exit

## Migration Path

If migrating from subprocess spawn to pending_tasks:
1. Replace `self.spawn_profile_agent(...)` with `self._enqueue_pending(profile, event_id, topic, payload)`
2. Create cron jobs for each profile that needs to consume
3. Delete the old `spawn_profile_agent` method and all subprocess/retry/DLQ code from the daemon
4. Remove ThreadPoolExecutor from the daemon (no longer needed)
