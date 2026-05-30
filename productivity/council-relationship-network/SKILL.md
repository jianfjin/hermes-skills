---
name: council-relationship-network
description: "16-person (+ CTO) council relationship graph with affinity engine — real-world edges, event-driven affinity changes, debate influence mechanics, and narrative state transitions."
version: 1.0.0
---

# Council Relationship Network

A weighted directed graph tracking relationships between all 16 Paperclip Inner Circle members (+ CTO 峰哥). Affinity scores (-100 to +100) evolve through council events. Thresholds trigger roleplay state transitions.

## Data Model

`pathfinder/council/network.py`:

- **Person**: member_id, name, title, model, language, personality traits
- **Relationship**: directed edge (from→to) with affinity, history, real_world_connection
- **EventType**: 22 event types covering voting, collaboration, competition, hardware
- **RelationState**: 9 levels from FEUD (< -75) to DEEP_ALLIANCE (> +80)

## Real-World Edges

120+ pre-seeded directed edges based on Wikipedia/LinkedIn research. Key dynamics:

| From | To | Affinity | Connection |
|------|----|:-------:|------------|
| Fei-Fei | Andrej | +40 | PhD advisor (Stanford) |
| Musk | Sam | -45 | OpenAI co-founder → lawsuit |
| Lisa | Jensen | -25 | Market rivals, distant relatives |
| Linus | Jensen | -35 | NVIDIA "middle finger" incident |
| Andrej | Musk | +15 | Tesla Autopilot, wary of volatility |
| Guido | Dijkstra | +20 | Dutch computing heritage |
| Demi | Jensen | +10 | Pika Labs runs on NVIDIA GPUs |
| Sam | Demi | +15 | YC ecosystem connection |

See `REAL_WORLD_EDGES` in network.py for the full list.

## Affinity Mechanics

### Event Deltas

| Event | Delta | Trigger |
|-------|:-----:|---------|
| AGREE_VOTE | +3 | Same vote |
| DISAGREE_VOTE | -2 | Opposite vote |
| PUBLIC_PRAISE | +8 | Compliment in debate |
| PUBLIC_CRITICISM | -10 | Attack in debate |
| DEFENDED | +15 | Defended someone |
| BETRAYED | -25 | Switched sides |
| SHIPPED | +18 | Delivered working artifact (Demi) |
| CODE_REVIEW_APPROVAL | +8 | Approved merge (Linus) |
| MENTORSHIP | +5 | Advisor relationship (Fei-Fei) |
| SIDED_WITH_ENEMY | -15 | Supported opponent (Sam) |
| STOLEN_CREDIT | -20 | Took credit (Sam) |
| TALENT_POACHED | -20 | Hired away team (Lisa) |
| CHIP_SUCCESS | +10 | Hardware milestone (Lisa) |

### Personality Modifiers

- **VOLATILE** (1.5x amplify): musk, linus, jobs, sam, dijkstra, jensen
- **GRUDGE_HOLDERS** (0.5x negative decay): linus, jobs, dijkstra
- **Fei-Fei dampener**: 0.7x (measured, slow to shift)
- **Musk asymmetry**: +1.5x positive, -1.2x negative

### Decay

- Positive edges: 2%/cycle toward 0
- Negative edges: 1%/cycle (grudges last longer)
- Grudge holders: 0.5x normal decay rate

### Special Mechanics

- **Betrayal floor**: Once betrayed, affinity capped at -40
- **Hysteresis**: After feud, recovery capped at 50% of pre-feud peak
- **Oscillation damping**: Volatile-volatile pairs max 20pt swing/cycle
- **Third-party propagation**: 5% of edge changes propagate to adjacent edges
- **Diminishing returns**: Same event repeated = 80% of previous delta

## State Transitions

| State | Range | Meaning |
|-------|:-----:|---------|
| FEUD | < -75 | Irreconcilable — mutual veto, no co-authorship |
| HOSTILE | -55 to -75 | Active blocking of proposals |
| RIVAL | -35 to -55 | Competing, edge in debates |
| COLD | -20 to -35 | Distant, minimal interaction |
| NEUTRAL | -20 to +20 | Baseline |
| CORDIAL | +20 to +35 | Professional respect |
| RESPECT | +35 to +50 | Productive disagreement possible |
| WARM | +50 to +65 | Collaboration preference |
| ALLIANCE | +65 to +80 | Co-sign proposals, defend publicly |
| DEEP_ALLIANCE | > +80 | Unconditional trust, co-invest resources |

## Narrative Triggers

When thresholds are crossed, narrative events fire:

- **ALLIANCE_THRESHOLD (70)**: Co-signing, private meetings begin
- **DEEP_ALLIANCE (85)**: Co-investment, unconditional defense
- **HOSTILE_THRESHOLD (-55)**: Active opposition in debates
- **FEUD_THRESHOLD (-75)**: Mutual veto on everything

## Usage

```python
from pathfinder.council.network import Person, Relationship, AffinityEngine, EventType

engine = AffinityEngine()
# Process a council vote where Musk and Sam agreed
new_affinity, triggers = engine.process_event(
    rel=musk_to_sam_edge, event=EventType.AGREE_VOTE, cycle=42
)
# Apply decay between sessions
engine.decay(musk_to_sam_edge)
```

## Onboarding a New Member

See `inner-circle-debate` skill reference: `references/creating-a-new-council-profile.md`. After creating the profile, add the new member's real-world edges to `REAL_WORLD_EDGES` in `pathfinder/council/network.py`.

## Pitfalls

- **Affinity changes during debate are immediate** — agents should reference their current affinity when voting
- **Decay runs BETWEEN sessions**, not during
- **DEEP_ALLIANCE pairs auto-second each other's proposals** unless core principles conflict
- **FEUD pairs cannot be assigned to the same subcommittee**
- **Real-world edges are pre-seeded but evolve** — the initial +40 for Fei-Fei→Andrej can shift based on council events
- **Volatile personalities need oscillation damping** — without it, musk↔sam can swing 50 points in one cycle
