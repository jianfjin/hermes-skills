# Plan Review Debate Pattern

When the user presents a technical plan for council audit, use this focused 6-seat debate pattern. Not a technology choice — a plan quality review.

## When to use

- User says "审核一下这个计划" or "review this plan"
- The plan has concrete phases, time estimates, and technical choices
- The question is "is this the right plan?" not "which technology should we use?"

## Seat Selection

Use Product + Architecture hybrid subset (6 seats):

| Seat | Role | Question |
|------|------|----------|
| Jobs (CPO) | Product/UX | Is this what users need? What's missing from user perspective? |
| Musk (CVO) | First principles | What's the irreducible core? Strip away everything non-essential. |
| Guido (CLA) | Data model / API | Are the contracts clean? Are function signatures honest? |
| Linus (Arch) | Architecture | Is the tech approach sound? Where are the hidden complexity traps? |
| Xiaolong (Eng) | Feasibility | Can this actually be built in the estimated time? What's the riskiest phase? |
| Xuefeng (CSA) | Cost audit | Is the estimate honest? Where's the padding? What's the MVP? |

## Brief Structure

The debate brief should be a compressed version of the plan, focusing on:
1. What the plan proposes to build (1-2 sentences)
2. Phase breakdown with time estimates
3. Key technical constraints or choices
4. No raw URLs, no external references — CTO pre-digests everything

## Expected Outcome

Nearly always results in **significant scope reduction**:
- Plans tend to over-engineer (Musk's "factor of five" rule)
- Time estimates tend to include padding (Xuefeng's cost audit)
- Phases that should be single-sections get split into separate artifacts (Linus: "integration phase admits views shouldn't have been separate")

Typical result: 5d plans → 2d revised plans. The council identifies ~3d of "foam" (padding, over-separation, unnecessary integration work).

## Worked Example

2026-05-19: Pathfinder Visualization Plan audit. 6 seats, 6/6 rejected original 5d plan. Revised to 2d plan with: schemas.py (dataclass contracts), adapter.py (validation), single HTML renderer (5 vertical sections), inline SVG path graph.

Full record: `scailed_wp4/docs/records/2026-05-19-council-debate-visualization-plan.md`
