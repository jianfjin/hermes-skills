# Warm Standby Pattern — Deferred Implementation Decisions

**Context:** 2026-05-29 Hermes Event Bus debate
**Problem:** A technically sound, fully-reviewed, unanimously-approved proposal that nobody has implemented for >1 year.

## Signal: When to Use This Pattern

- Design is correct and all reviewers agree
- No P0/P1 production pain justifies implementation now
- Current scale doesn't need the feature (e.g., 12 agents, O(n²)=66 channels — not enough)
- Implementation cost is real and near-term benefit is marginal
- "The right solution at the wrong time"

## The Pattern

1. **Full design + review** — Complete the spec, get the vote. Do not skip quality.
2. **Warm standby status** — Document as APPROVED but NOT IMPLEMENTED. Mark trigger condition.
3. **Trigger condition** — Quantitative threshold that justifies implementation (e.g., "profile count ≥ 8").
4. **Lock the spec** — No further design iteration until trigger fires. Prevent scope creep.
5. **Rotate ownership** — Assign a nominal owner who keeps the spec alive without building it.

## Trigger Condition Design

Bad trigger: "when we need it" (too vague)
Good trigger: "when profile count ≥ 8" (measurable, automatable)

## Key Quotes from 2026-05-29 Debate

- Linus: "This is toy time, not product time."
- Dijkstra: "Spec correctness and engineering correctness are two different things."
- Guido: "Unless you really need it, don't add it. Python's asyncio waited 3 years."
- Fei-Fei + Karpathy: "Save the spec. Mark it WARM STANDBY. When Hermes needs it, the implementation is ready."
