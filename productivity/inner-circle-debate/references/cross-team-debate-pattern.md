# Cross-Team Joint Debate Pattern

Used when VM and local teams each produce a plan, then compare, then joint-vote.

## Pattern

```
Phase 1: VM council produces plan (6-8 seats, parallel agents)
Phase 2: Local team produces competing plan (via tmux/webhook notification)
Phase 3: Pull both plans, produce COMPARISON document (markdown + HTML)
Phase 4: Joint council vote — all seats from both teams vote on each item
Phase 5: Emperor decides; winning plan adopted
Phase 6: Rebuttal round if contested; re-audit after fixes
```

## Real Examples

### DR Plan (2026-05-20)
- VM council: pg_dump+WAL→cloud, €1,816, NO replica (6/0)
- Local team: 3-layer backup+streaming replica Local→VM, €12,000+
- Comparison: docs/plans/2026-05-20-disaster-recovery-comparison.md
- Joint vote: 15/0 adopted VM plan
- R2 free tier reduced budget to €0

### Schema Drift (2026-05-20)
- VM council: normalize layer in upstream.py NOW (5/5)
- Local team: adopted with conditions (Wasabi→R2, 4-layer→verify, budget)
- Joint vote: 15/0 unanimous

## Key Rules
1. Both teams produce independently before sharing
2. Comparison document MUST be written before joint vote
3. Every item voted separately (PASS/FAIL with reason)
4. Emperor holds veto (Charter §7a)
5. All decisions archived in docs/records/ and docs/plans/
