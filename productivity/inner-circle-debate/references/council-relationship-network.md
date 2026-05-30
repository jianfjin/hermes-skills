# Council Relationship Network — Affinity Engine

Code: `pathfinder/council/network.py`

## Overview

15 council members form a directed graph. Each pair has an affinity score (-100 to +100).
Affinity changes based on council events. Thresholds trigger state transitions.

## States (9 levels)

| State | Range | Meaning |
|-------|-------|---------|
| FEUD | < -75 | Irreconcilable — mutual veto, no co-authorship |
| HOSTILE | -55 to -75 | Opposition — active blocking |
| RIVAL | -35 to -55 | Competing, edge in debates |
| COLD | -20 to -35 | Distant |
| NEUTRAL | -20 to +20 | Baseline |
| CORDIAL | +20 to +35 | Professional respect |
| RESPECT | +35 to +50 | Productive disagreement enabled |
| WARM | +50 to +65 | Collaboration preference |
| ALLIANCE | +65 to +80 | Co-sign proposals, defend publicly |
| DEEP_ALLIANCE | > +80 | Unconditional trust, co-invest |

## Event Types (22)

Council: agree_vote(+3), disagree_vote(-2), public_praise(+8), public_criticism(-10), defended(+15), betrayed(-25), ignored(-4)
Collaboration: collaboration(+12), shipped(+18), code_review_approval(+8), joint_paper(+10), alliance_formed(+12), mentorship(+5), data_shared(+7)
Conflict: sided_with_enemy(-15), stolen_credit(-20), talent_poached(-20), shared_enemy(+3/cycle)
Hardware: chip_success(+10), chip_failure(-7), resource_shared(+3), resource_denied(-10)

## Mechanics

- **Asymmetric decay**: positive edges 2%/cycle, negative 1%/cycle (grudges last longer)
- **Grudge holders**: Linus, Jobs, Dijkstra — negative decay at 0.5x normal
- **Betrayal floor**: once betrayed, affinity capped at -40 forever (Musk)
- **Hysteresis**: after feud, recovery capped at 50% of pre-feud peak
- **Oscillation damping**: volatile-volatile pairs max 20pt swing/cycle
- **Third-party propagation**: 5% of edge changes propagate to adjacent edges
- **Diminishing returns**: repeated same-type events: 80% of previous delta

## Personality Modifiers

- VOLATILE (1.5x): musk, linus, jobs, sam, dijkstra, jensen
- Fei-Fei dampener: 0.7x (measured, slow to shift)
- Musk asymmetry: +1.5x positive, +1.2x negative

## Real-World Seed Edges

~120 directed edges pre-seeded from Wikipedia/LinkedIn research.
Key relationships: Fei-Fei↔Andrej (PhD advisor), Musk↔Sam (OpenAI → lawsuit -60),
Lisa↔Jensen (distant relatives + market rivals -25), Linus↔Jensen (NVIDIA middle finger -35).

## Usage in Debates

When launching a council debate, the affinity engine can inform:
- Which members are likely to agree (check alliance state)
- Which pairs may produce conflict (rivalry/hostile states)
- How debate outcomes will shift relationships (process_event after vote)
