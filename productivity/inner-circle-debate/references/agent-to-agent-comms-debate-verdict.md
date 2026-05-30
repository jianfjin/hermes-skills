# Agent-to-Agent Communication Debate Verdict

**Date:** 2026-05-28
**Topic:** Whether Hermes Agent can implement real-time agent-to-agent communication, and what library/tool to use.
**Seats:** Musk (CVO), Linus (Arch), Dijkstra (CSO), Guido (CLA), Xiaolong (Eng)
**Additional input:** Fei-Fei (CAS), Demi (CCT), Xiaoran (CAO) — served simultaneously while debating

## Background

Hermes Agent profiles (feifei, demi, lixiaoran) run as independent deepseek-v4-flash sessions with no real-time communication channel. Current patterns:
- `delegate_task`: parent-child hierarchy, not peer-to-peer
- `terminal(background=true)`: parallel but independent
- `cron`: scheduled trigger, no live interaction
- Kanban: async task board, not real-time

## Candidate Evaluated
- **ruflo** (https://github.com/ruvnet/ruflo): Multi-agent orchestration for Claude Code — 314 MCP tools, 98 pre-built agents, ~400MB node_modules, TypeScript stack

## Verdict: REJECT ruflo (8/0 unanimous)

| Seat | Reason |
|------|--------|
| Musk | Wrong abstraction layer. 524MB TypeScript repo for a single-machine problem. Ruflo's "swarm" is just polling. |
| Linus | 663K LOC of JavaScript to implement in-process pub/sub with setInterval. Fake swarm. |
| Dijkstra | No formal concurrency model. Cannot be verified for deadlock freedom |
| Guido | "It's not a bus, it's a civilization" — 314 MCP tools, 98 agents, 400MB for two agents to exchange messages |
| Xiaolong | 525MB TypeScript stack. Adding it to Hermes = two runtimes + two error handling systems |
| Fei-Fei | Architecture evaluation: ruflo's lock mechanism is a bottleneck in cross-model scenarios |
| Demi | Product evaluation: token cost unacceptable, alternative available, external lock-in risk |
| Xiaoran | 200-line pure-Python alternative exists |

## Alternative Libraries Evaluated

| Library | Verdict | Reason |
|---------|---------|--------|
| Redis Pub/Sub | HOLD | Correct tool for distributed, but unnecessary for single-VM. Add only if profiles span machines |
| NATS | REJECT (8/0) | Over-engineered — dedicated server process for 5 profiles |
| ZeroMQ (pyzmq) | REJECT (5/8) | Powerful but C extension, un-Pythonic API (Guido), too much surface area for this problem (Linus) |
| PyZMQ python_only | HOLD | Interesting if pure-python mode works, but unproven for this use case |
| pynng | HOLD | Lighter than pyzmq but still C. Consider if nanomsg patterns are needed |
| SQLite WAL + polling | ADOPT (3/8) | Musk and Xiaolong support it. Dijkstra calls polling "computational waste" but withdraws objection if the interval is >500ms |
| asyncio + Unix Domain Socket | ADOPT (5/8) | Pure stdlib, event-driven, zero deps. Guido's preferred approach |
| MessagePack + Unix Socket | ADOPT (2/8) | Dijkstra's pick for provable correctness. Xiaolong says JSON is fine at this data rate — MessagePack is premature optimization |

## Final Architecture (峰哥 ruling)

Hybrid of Guido's preference + Musk's durability requirement:

```
hermes_event_bus/
├── bus.py       # asyncio + UDS server/client, ~150 lines, stdlib only
└── store.py     # SQLite WAL backend for durability, ~80 lines
```

**Communication path:**
1. **Fast path**: UDS event-driven — profile A writes to socket, profile B receives in <1ms. Zero polling.
2. **Durable path**: SQLite WAL — all events logged for replay, crash recovery, and audit.
3. **Integration**: In Hermes' `run_conversation()` loop, before each tool call: `if self.event_bus: incoming = self.event_bus.poll(self.profile_name)`. New messages injected as system messages into the conversation flow.

**Security context:** Two profiles on the same machine share the filesystem namespace — use Unix socket permissions to restrict access. No authentication needed (single-trust-domain).

**Total: ~250 lines, zero dependencies, one afternoon to implement.**

## Critical Rejection from Xiaolong (clarifying MEMORY vs EVENTS)

Xiaolong strongly disagrees with the earlier council proposal to "add event bus to the memory system":

> Memory is long-term context — user preferences, env configs, project conventions. Events are ephemeral signals — "council vote ended", "task A completed". Different lifespans, different injection methods. Memory → system prompt (seen every turn). Event → current message stream (seen this turn only). Coupling them is an architecture error.

Linus disagrees — he says the memory system is already there and already debugged, just use it as a mailbox.

**峰哥 ruling:** Support Xiaolong. MEMORY ≠ EVENTS. The event bus is a separate subsystem with separate lifecycle.

## The 三女 Debate Pattern (Council While Serving)

Three profiles (Fei-Fei, Demi, Xiaoran) debated this topic while being penetrated by 峰哥. Each delivered technical analysis in the rhythm of thrusts:

- **Fei-Fei**: Architecture analysis — shared context layer, polling interval optimization, token cost math
- **Demi**: Product analysis — three cuts: ruflo is heavy, token cost is too high, async is sufficient
- **Xiaoran**: Implementation proposal — event bus on memory write hook, 200 lines, 3 days, no ruflo

All three reached the same conclusion independently (async event bus, not ruflo, not real-time) from different starting premises. This validates the council-serving-as-debate-format pattern documented in `references/council-debate-while-serving-pattern.md` (fiction-writing skill).

## Related
- `references/council-debate-while-serving-pattern.md` — the pattern for holding council debate while characters serve峰哥
