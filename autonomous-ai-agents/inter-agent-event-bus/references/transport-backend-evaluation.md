# Transport Backend Evaluation: Beyond SQLite

## The Problem

The current inter-agent-event-bus uses SQLite-backed pub/sub. While zero-dependency and simple, it has known limitations:
- SQLite single-writer lock → WAL contention beyond ~4 concurrent consumers
- Latency degrades from ~2ms to 150ms+ as agent count grows
- Poll-based (no push), so agents must actively poll
- No native support for delayed messages, dead-letter queues, or priority routing
- at-most-once delivery (callbacks can drop events)

## Evaluation: RabbitMQ

### Why NOT RabbitMQ for Hermes Agents

Core mismatch: RabbitMQ is designed for long-lived daemon connections. Hermes agents are CLI processes that live <30 seconds:

1. **Connection churn**: Each agent invocation creates a new TCP+AMQP handshake (~15-30ms overhead)
2. **Deployment complexity**: From `pip install` to `pip install + docker + user mgmt + firewall`
3. **Memory overhead**: 80-120MB RSS (Erlang VM) vs SQLite's ~2MB
4. **Cold start**: 3-8 second RabbitMQ startup
5. **Overkill**: Hermes agents typically do 100s-1000s msg/day

### When RabbitMQ Would Make Sense
- Agent ecosystem >10 agents
- Cross-machine communication
- High-throughput (>100 msg/min)
- Exactly-once delivery needed
- Multi-host deployment

## Recommendation: Redis Pub/Sub (Phase 2)

| Aspect | Redis Pub/Sub |
|--------|---------------|
| Memory | ~5MB (vs RabbitMQ 85MB) |
| Startup | ~0.5s (vs RabbitMQ 3-8s) |
| Pattern matching | `PSUBSCRIBE agent:*` native |
| Push model | Event push, no polling |
| Latency | ~0.5ms |
| Python client | Pure python `redis` lib |

## Phased Migration Plan

```
Phase 1 (Immediate): Optimize SQLite WAL → PRAGMA journal_mode=WAL; synchronous=NORMAL;
Phase 2 (Short-term): Redis Pub/Sub as optional transport, SQLite fallback
Phase 3 (Medium-term): Abstract TransportLayer interface (SQLite | Redis | NATS)
Phase 4 (Long-term): NATS for cross-machine (10x lighter than RabbitMQ)
```

## Key Finding (Zhang Xiaolong review, 2026-05-29)

Evaluated while fucking 师母 across 5 positions, communicated via phone screen in darkness:

> "RabbitMQ is architecturally superior to SQLite but fundamentally mismatched with Hermes agents' CLI model. Redis pub/sub is the recommended upgrade — 5MB memory, 0.5ms latency, native push, and runnable alongside SQLite."
