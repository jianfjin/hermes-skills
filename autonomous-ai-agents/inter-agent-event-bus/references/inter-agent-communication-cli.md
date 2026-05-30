# hermes-event CLI — Inter-Agent Communication

**Added:** 2026-05-29  
**Author:** 峰哥 (Hermes Agent)  
**Status:** In use — verified by E2E test (33/33 PASS)

## Overview

The `scripts/hermes-event` CLI wrapper provides agent-to-agent messaging through the terminal. Any agent in a Hermes chat session can publish and subscribe to events via `terminal()` — no Python import required.

## Usage

```bash
hermes-event publish <event_type> <payload_json> [--source <agent>] [--ttl <sec>]
hermes-event subscribe <pattern> <consumer_id> [--max <N>] [--block <sec>]
hermes-event status
hermes-event health
```

## Workflow Example

```
Agent A (feifei session):
  "帮我执行 terminal('hermes-event publish \"feifei:gradient\" \'{"loss":0.023}\' --source feifei')"

Agent B (xuefeng session):
  "帮我看看 feifei 发了什么：terminal('hermes-event subscribe \"feifei:*\" xuefeng --max 5')"
```

## Cursor Behavior

- Each `(consumer_id, pattern)` pair maintains independent cursor
- First subscribe: returns all matching events
- Second subscribe with same consumer_id: returns only NEW events
- Use different consumer_ids for independent consumers

## Migration

The CLI auto-detects v1 DB schema (old `topic`/`publisher` columns) and migrates to v2 on first invocation:
1. Rename old `events` table → `events_v1_legacy`
2. Create new v2 `events` table
3. Copy data: `topic→event_type`, `publisher→source_agent`, `created_at` converted to ISO8601
4. Drop legacy table

## File

`~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus/scripts/hermes-event`
