# Joint Two-Team Debate Pattern (2026-05-20, DR debate)

Two independent agent teams produce competing proposals, compare, and joint-vote.
Used for SCAILED WP4 DR/backup/replication debate. 16 seats across two teams.

## When to use

- High-stakes decision where two independent perspectives reduce blind spots
- Both teams have access to the same codebase and docs
- User wants formal comparison before deciding

## Pattern

### Phase 1: Independent proposals
1. Each team produces a plan independently
2. Plans pushed to shared GitHub repo
3. Both sides read the other's plan

### Phase 2: First-pass debate + rebuttal
1. Team A convenes council to debate Team B's plan
2. Team A produces rebuttal with vote table on each disputed item
3. Rebuttal pushed; Team B reads

### Phase 3: Joint vote
1. Both teams re-convene for second round
2. Each agent votes on every contested item
3. Votes tallied across both teams
4. Unanimous/supermajority items = settled

### Phase 4: Implementation + Audit
1. Winning plan implemented
2. Losing team audits
3. Bugs fixed → re-audited → final sign-off

## Key rules

- No premature merging at Phase 1
- Vote tables mandatory on every dispute
- Rebut, don't re-argue
- Joint vote is final authority (user decides)
- Budget comparison tables persuasive for EU grants

## Worked example

SCAILED WP4 DR debate: €12,000 streaming replica vs €1,816 pg_dump vs €0 R2.
Full documents in scailed_wp4/docs/plans/2026-05-20-*.
