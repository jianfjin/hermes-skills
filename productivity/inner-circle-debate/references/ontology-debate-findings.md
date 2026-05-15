# Ontology Debate Findings (2026-05-15)

7-seat focused debate evaluating whether Palantir Ontology should be adopted for SCAILED WP4 Pathfinder.

## Consensus: Pathfinder IS Already an Ontology

The mapping is trivial — this is relabeling, not reinvention:

| Palantir Primitive | Pathfinder Equivalent | Verdict |
|-------------------|---------------------|---------|
| Object Types | Stakeholder profiles, Roadmap nodes | Already modeled |
| Property Types | Maturity scores, compliance status | JSONB fields |
| Link Types | DAG edges | Apache AGE |
| Action Types | Recommendations | 🟢 GENUINE VALUE-ADD |
| Functions | Solver, compliance checker | Python functions |
| Interfaces | Stakeholder polymorphism | Protocol classes |

## Actions (What We Adopt)

### Action Writeback (7/7 consensus — the only hard increment)

Current: Pathfinder emits recommendations then black hole. No feedback loop.
Fix: Recommendation lifecycle state machine (pending, accepted, executed, verified).
Turns Pathfinder from static rulebook into operational system.

### YAML to Pydantic Codegen (3/7 — Guido, Linus, Jobs)

200-line Python script. pre-commit hook. Eliminates hand-sync bugs.
Phase 1 late (M6-M8). Not MVP-critical per Xiaolong.

## Rejections (What We Don't Do)

- Full Palantir model: overengineering for our scale
- Walk-up tools replacing Vue frontend: keep our bespoke UI
- Marketplace rule packages: one regulatory framework, build it once
- FDE as permanent embedded role: costs explode

## FDE Decision

- Xiaolong: NOT him (communication gap)
- Recommendation: Feng Ge does 1-2 on-site workshops at Epidata/CHARITE. Hire Technical Business Analyst if scaling to multiple clients.

## Seat Votes

| Seat | Full Ontology? | Action Writeback? | Codegen? | FDE Self-Nom? |
|------|---------------|-------------------|----------|---------------|
| Musk | Already is one | Support | Skeptical | — |
| Dijkstra | Fix fundamentals | Support | No | — |
| Linus | 20% only | Support | Yes | — |
| Guido | Concepts yes | Support | Yes | — |
| Jobs | Plumbing only | Strong yes | Neutral | "You are the FDE" |
| Xuefeng | Hard no | Support | No | No |
| Xiaolong | Only Writeback | Yes | No (MVP noise) | No |
