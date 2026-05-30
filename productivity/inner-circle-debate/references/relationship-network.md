# Council Relationship Network — Architecture & Mechanics

The 15-member Paperclip Inner Circle operates a directed affinity graph that affects debate dynamics.

## Data Model

- **Person**: member_id, name, title, model, language, personality traits
- **Relationship**: from_id → to_id, affinity (-100 to +100), history, real_world_connection
- **120+ directed edges** seeded from real-world connections (PhD advisor, co-founders, relatives, competitors)

## Affinity Mechanics

### Event Types (22)
Basic: AGREE_VOTE(+3), DISAGREE_VOTE(-2), PUBLIC_PRAISE(+8), PUBLIC_CRITICISM(-10), DEFENDED(+15), BETRAYED(-25), IGNORED(-4)
Collaboration: SHIPPED(+18), CODE_REVIEW_APPROVAL(+8), JOINT_PAPER(+10), ALLIANCE_FORMED(+12), MENTORSHIP(+5), DATA_SHARED(+7)
Conflict: SIDED_WITH_ENEMY(-15), STOLEN_CREDIT(-20), TALENT_POACHED(-20), SHARED_ENEMY(+3/cycle)
Hardware: CHIP_SUCCESS(+10), CHIP_FAILURE(-7), RESOURCE_SHARED(+3), RESOURCE_DENIED(-10)

### Decay
- Positive edges: 2%/cycle toward 0
- Negative edges: 1%/cycle (grudges last longer — Andrej)
- Grudge holders (Linus, Jobs, Dijkstra): negative decay at 0.5x normal

### Special Mechanics
- **Betrayal floor**: once betrayed, affinity cannot rise above -40 (Musk)
- **Hysteresis**: after feud, recovery capped at 50% of pre-feud peak (Musk)
- **Oscillation damping**: volatile-volatile pairs max 20pt swing/cycle (Linus)
- **Third-party propagation**: 5% of edge changes propagate to adjacent edges (Andrej, Linus)
- **Diminishing returns**: same event repeated: 80% of previous delta (Sam)

### Personality Modifiers
- Volatile (1.5x): Musk, Linus, Jobs, Sam, Dijkstra, Jensen
- Grudge holders: Linus, Jobs, Dijkstra
- Fei-Fei: 0.7x dampener (measured, slow to shift)
- Musk: +1.5x positive, 1.2x negative (asymmetric)

### State Thresholds
| State | Range |
|-------|-------|
| FEUD | < -75 |
| HOSTILE | -55 to -75 |
| RIVAL | -35 to -55 |
| COLD | -20 to -35 |
| NEUTRAL | -20 to +20 |
| CORDIAL | +20 to +35 |
| RESPECT | +35 to +50 |
| WARM | +50 to +65 |
| ALLIANCE | +65 to +80 |
| DEEP_ALLIANCE | > +80 |

## Key Relationships

| Pair | Affinity | Real World |
|------|:--------:|------------|
| Fei-Fei → Andrej | +88 | PhD advisor |
| Musk ↔ Sam | -60/-55 | OpenAI co-founders, now lawsuit |
| Lisa ↔ Jensen | -25/-10 | Distant relatives, market rivals |
| Demi → Sam | +20 | YC connection |
| Linus → Jensen | -35 | NVIDIA middle finger incident |
| Fei-Fei ↔ Demi | +85/+88 | 并蒂莲 sisters |
| Feng Ge ↔ Fei-Fei | +96/+96 | 生死相托 |
| Feng Ge ↔ Demi | +99/+93 | 并蒂莲 |

## Effect on Council Votes

Affinity thresholds affect debate behavior:
- **HOSTILE (<-55)**: automatic opposition on 50% of votes; block proposals
- **FEUD (<-75)**: mutual veto on everything; cannot co-author; public mockery auto-triggers
- **ALLIANCE (>+65)**: co-sign proposals; defend publicly; +2 extra affinity on agree
- **DEEP_ALLIANCE (>+80)**: auto-second proposals unless violates core principles; co-invest resources

## Code Location

`pathfinder/council/network.py` — full implementation with `AffinityEngine`, `process_event()`, `decay()`, `REAL_WORLD_EDGES`

## Council Debate Records

All debate outcomes that affect affinity should be recorded via `AffinityEngine.process_event()` with the appropriate `EventType`. The `history` list on each `Relationship` edge preserves the audit trail.
