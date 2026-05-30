# Visualization Plan Audit — 6-seat Product+Architecture Debate (2026-05-19)

The council audited a 6-phase, 5-day Pathfinder visualization plan. All 6 seats voted against the original plan. Key findings:

## What went wrong in the original plan

1. **Three separate HTML files + integration phase** — anti-pattern. Jobs: "Tabs hide information." Musk: "The integration phase is an admission the views shouldn't have been separate." One self-contained HTML file with vertical scroll is the correct approach.

2. **SVG DAG from scratch (1.5 days)** — Xiaolong: "Pure hand-written layout — crossing minimization alone is a master's thesis." The plan over-estimated SVG layout difficulty while under-estimating it simultaneously. Graphviz CLI → Python post-processing is the pragmatic middle ground.

3. **Dict[str, Any] adapter layer** — Guido: "Template receiving mutable dicts that Jinja macros might accidentally modify." Frozen dataclasses as view models are the correct contract.

4. **5-day estimate padded to 2-day reality** — Xuefeng identified 3 days of "泡沫" (bubbles): adapter layer padding (0.5d), SVG DAG over-estimate (1.25d), evidence cards as separate phase (0.5d), integration panel (0.5d).

## The correct pattern

```
Phase 1 (1d): Single HTML generator
  GET /report?format=html → self-contained HTML
  4 vertical sections: Readiness Score, Blockers, Path, Evidence
  Data flow: dict → adapter → frozen dataclass → template

Phase 2 (0.5d): Evidence deep-dive
  Per-rule condition match comparison + compliance refs

Phase 3 (0.5d): Path graph
  graphviz CLI → SVG OR text-based layer diagram
  Subgraph only (not full 1000-node DAG)
```

## Voting record

| Seat | Vote | Key reason |
|------|------|------------|
| Musk (CVO) | ❌ | One file, vertical scroll, no tabs |
| Jobs (CPO) | ❌ | Missing narrative + "What If" interaction |
| Xuefeng (CSA) | ❌ | 3d padding identified (cost audit) |
| Xiaolong (Eng) | ❌ | SVG DAG layout is a minefield |
| Guido (CLA) | ❌ | Data contracts undefined |
| Linus (Arch) | ⚠️ | Approve SVG, collapse phases |

Full debate record: `scailed_wp4/docs/records/2026-05-19-council-debate-visualization-plan.md`
