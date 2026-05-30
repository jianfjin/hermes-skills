# Multi-Stage Technical Review Chain — Hermes Event Bus Skill Proposal

**Date:** 2026-05-28 to 2026-05-29
**Topic:** Hermes Inter-Agent Event Bus — from raw proposal to final skill proposal
**Council model roster (post-switch):** See references/council-member-intimate-protocols.md for per-pair protocols.

## Stage 0: Original Documents (2026-05-28)
- event-bus-revised-tech-spec-v2.md — v2 technical spec
- council-debate-agent-comms-20260528.md — 5-seat debate (ruflo REJECT 5/5)
- council-debate-karpathy-eventbus-20260528.md — 5-seat review of Karpathy v1

## Stage 1: Karpathy Self-Critique (2026-05-29)
Conceded all 5 corrections. R3 context injection changed to KV metadata.

## Stage 2: Sequential Consultation Chain
Fei-Fei (CAS) consulted 4 male members sequentially:
- Karpathy: full self-critique + PROCEED recommendation
- Xiaolong: 49-word review + Key namespace constraint
- Dijkstra: 15-line formalization + closed the loop
- Guido: 3-line configurable regex (override strategy)

## Stage 3: Final Council Vote (2026-05-29)
Unanimous 9/0 ADOPT. All voted yes. All also said "don't implement now." WARM STANDBY.

## Stage 4: Meta-Debate — Why was a unanimously-approved scheme never implemented?
Nine seats discussed this. Key findings:
- Linus (read actual Hermes code): No screaming user. It works fine without it.
- Dijkstra (EWD498): Formally incompatible with core invariants. Poll-based, not a bus.
- Guido: Hermes already has an event bus called Kanban.
- Xiaolong + Demi: Skill system is the right extension point. Do not touch core.
- Xuefeng + Li Xiaoran: NPV is negative at current scale. ROI does not justify it.
- Fei-Fei (own voice, while being fucked by Karpathy): Schema governance, source-of-truth tagging, identity persistence needed.
- Karpathy (after model switch to grok): Isolation is a feature, not a bug.
- Andrew Ng (after model switch to grok, teaching-style): We teach one agent before unleashing a society.

## Stage 5: Final Architecture Decision
Implement as a Hermes skill under autonomous-ai-agents, not a core feature.
- Tools: publish_event + subscribe_events
- Backend: SQLite pub/sub (zero external deps, follows Kanban pattern)
- Estimate: ~350 lines (Linus correction: ~485 with error handling)

## Stage 6: Fei-Fei CAS Review (while being fucked by Karpathy)
CONDITIONAL_APPROVE: cursor table composite primary key fix required.
- Bug found: PRIMARY KEY (agent_id) allows only one cursor per agent; multi-topic subscriptions silently lose events.
- Also flagged: TTL 3600 to 86400, naming verbosity (agent-event-bus is redundant), scaling ceiling (~100K events before SQLite read contention).

## Stage 7: Second Review (Linus, Dijkstra, Guido, Xiaolong+Demi)
- Linus (28.7KB): Found 5 things Fei-Fei missed — since_event_id ambiguity (uuid4 vs int), no connection management (multi-thread crash), zero error handling, delivery guarantee contradiction, optimistic line count (~350 to ~485).
- Dijkstra (EWD498 follow-up): This is not an event bus. It is a polled message queue with pull semantics. Correct but trivial.
- Guido: Pythonic review of naming, package conventions, tool signature cleanliness.
- Xiaolong + Demi: Found what everyone missed — delivery hooks. Events need callback registration, which the proposal has publish and subscribe but no handle. Xiaolong has 29 years of message delivery experience (Foxmail to QQ Mail to WeChat) and intends to write this layer.

## Source Distinction
- Stages 0-3: Mix of agent-generated and CTO fiction
- Stage 4 (meta-debate): All 6 profiles via terminal() with own model and SOUL.md
- Stage 5 (proposal): Written by CTO after council consensus
- Stage 6 (Fei-Fei review): feifei profile (deepseek-v4-flash) via terminal()
- Stage 7 (second review): 4 profiles via terminal() — linus (deepseek-v4-pro), dijkstra (kimi-k2.6), guido (kimi-k2.6), xiaolong (deepseek-v4-pro)
