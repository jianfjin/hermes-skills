# Council Relationship Network Architecture

Full specification of the affinity engine governing the 15-member Paperclip Inner Circle.

## Data Model

```
Person (15 nodes) ── Relationship (120+ directed edges) ── AffinityEngine
```

- **Person**: member_id, name, title, model, language, personality traits, mood, bio
- **Relationship**: from_id → to_id, affinity (−100 to +100), history of (event_type, delta) tuples, real_world_connection
- **AffinityEngine**: computes deltas, triggers state transitions, applies decay

## Relation States (9 levels)

| State | Range | Meaning |
|-------|-------|---------|
| FEUD | < −75 | Irreconcilable — mutual veto, no co-authorship |
| HOSTILE | −55 to −75 | Opposition — active blocking |
| RIVAL | −35 to −55 | Rivalry — competing, edge in debates |
| COLD | −20 to −35 | Cold — distant, minimal interaction |
| NEUTRAL | −20 to +20 | Baseline |
| CORDIAL | +20 to +35 | Professional respect |
| RESPECT | +35 to +50 | Productive disagreement, shared vision |
| WARM | +50 to +65 | Collaboration preference |
| ALLIANCE | +65 to +80 | Co-sign proposals, defend publicly |
| DEEP_ALLIANCE | > +80 | Unconditional trust, co-invest resources |

## Event Types (22)

Base deltas applied per event:

| Event | Delta | Source |
|-------|:-----:|--------|
| AGREE_VOTE | +3 | Core |
| DISAGREE_VOTE | −2 | Core |
| PUBLIC_PRAISE | +8 | Core |
| PUBLIC_CRITICISM | −10 | Core |
| DEFENDED | +15 | Core |
| BETRAYED | −25 | Core (triggers betrayal floor at −40) |
| IGNORED | −4 | Core |
| COLLABORATION | +12 | Core |
| SHIPPED | +18 | Demi |
| CODE_REVIEW_APPROVAL | +8 | Linus |
| JOINT_PAPER | +10 | Sam |
| ALLIANCE_FORMED | +12 | Sam |
| MENTORSHIP | +5 | Fei-Fei |
| DATA_SHARED | +7 | Fei-Fei |
| SIDED_WITH_ENEMY | −15 | Sam |
| STOLEN_CREDIT | −20 | Sam |
| TALENT_POACHED | −20 | Lisa |
| SHARED_ENEMY | +3/cycle | Musk |
| CHIP_SUCCESS | +10 | Lisa |
| CHIP_FAILURE | −7 | Lisa |
| RESOURCE_SHARED | +3 | Lisa |
| RESOURCE_DENIED | −10 | Lisa |

## Decay Mechanics

- Positive edges: 2% toward 0 per cycle
- Negative edges: 1% toward 0 per cycle (grudges last longer)
- Grudge holders (Linus, Jobs, Dijkstra): negative decay multiplied by 0.5×
- Betrayal floor: once BETRAYED event fires, affinity cannot rise above −40
- Hysteresis: after recovering from FEUD, affinity capped at 50% of pre-feud peak
- Oscillation damping: volatile-volatile pairs cannot swing >20 pts per cycle
- Third-party propagation: 5% of edge changes propagate to adjacent edges
- Diminishing returns: repeated same-type events get 80% of previous delta

## Personality Modifiers

- Volatile (1.5× all deltas): Musk, Linus, Jobs, Sam, Dijkstra, Jensen
- Grudge holders (0.5× negative decay): Linus, Jobs, Dijkstra
- Fei-Fei dampener (0.7× all deltas): Fei-Fei
- Musk asymmetry: +1.5× positive, +1.2× negative

## Post-Debate Processing

After each council debate with votes:

```python
engine = AffinityEngine()
for from_id, to_id in voting_pairs:
    if voted_same_way(from_id, to_id):
        engine.process_event(rel, EventType.AGREE_VOTE, cycle)
    else:
        engine.process_event(rel, EventType.DISAGREE_VOTE, cycle)
```

Log any state transitions in the debate record.

## Key Seeded Edges

Notable real-world relationships with non-zero affinity:

| From → To | Affinity | Connection |
|-----------|:--------:|------------|
| Fei-Fei → Feng Ge | 96 | 并蒂青莲, 生死相托 |
| Demi → Feng Ge | 99 | 70%专业崇拜, 渡劫扛雷 |
| Sam → Musk | −60 | OpenAI co-founder → lawsuit |
| Linus → Jensen | −35 | NVIDIA middle finger incident |
| Lisa → Jensen | −25 | Market rivals, distant relatives |
| Fei-Fei → Andrej | 88 | PhD advisor, 愧疚传承 |
| Linus → Dijkstra | 35 | Mutual legend respect |
| Demi → Sam | 25 | YC ecosystem, "shit friend" |

## Usage in Debates

1. **Load current state**: `from pathfinder.council.network import REAL_WORLD_EDGES, AffinityEngine`
2. **Run debate with agents**
3. **Process votes through engine**
4. **Log state transitions** in debate record
5. **Commit updated edges** if significant changes occurred
