# Codex Branch Audit Pattern (2026-05-18)

When an external agent (Codex, Claude Code, or similar) proposes changes via a git branch that conflicts with existing council-approved work, run a formal 8-seat audit before merging.

## Trigger

- An external agent opens a branch that modifies or deletes council-approved code
- The branch's diff shows significant deletions (>100 lines) or reversions of prior decisions
- The user expresses concern about the branch's correctness

## Pattern

1. **CTO pre-reads the branch diff**: `git diff main...origin/<branch> --stat`, then key files
2. **Write an audit brief** highlighting: what was deleted, what was added, the core disagreements
3. **Launch full 8-seat audit**: all non-CTO seats with role-specific questions
4. **Each seat evaluates from their domain**: Linus (architecture bugs), Xuefeng (contract/compliance risk), Jobs (product delivery), Dijkstra (correctness), Xiaolong (engineering pragmatism), Guido (Python ecosystem), Musk (first principles), Jensen (infrastructure)
5. **CTO tallies votes** and produces a MERGE/REJECT verdict
6. **If REJECT, absorb only specific fixes** — never the bulk deletions

## 2026-05-18 Worked Example

**Branch**: `feature/fix-pathfinder-v1-spec-drift`

**What it did**: Deleted 1,632 lines — middleware.py (332L), smoke_test.py (303L), verify_tasks.py (132L), test_d4_1_acceptance.py (232L), conftest.py, Makefile, pytest dependency, council reform plans.

**Key findings per seat**:
- Linus: Found 4 specific bugs in middleware. Fix is ~15 lines, not deletion.
- Xuefeng: Deletion removes D4.1 acceptance evidence. "Without audit logging, EHDS audit cannot pass."
- Jobs: "You don't prove compliance by erasing the exam."
- Dijkstra: "A correctable verifier is a rectifiable lattice; its absence is an unbounded uncertainty."
- Xiaolong: Middleware should be simplified not deleted; verify_tasks bug was a 1-line exit-code fix.
- Guido: pytest dependency removal breaks `make gate`. "Codex chose never, and broke the gate."
- Musk: "Hard reject. Absorb nothing from the deletion commit."
- Jensen: "Codex deleted the brake and claims the car is faster."

**Verdict**: 8/8 REJECT. Fixed 4 middleware bugs in-place (+15 lines) instead of deleting 332 lines.

**Key lesson**: When external agents propose "fixes", verify the fix is surgical (target the bug) rather than amputation (delete the whole module). A branch that deletes working infrastructure to fix configuration bugs should be rejected.
