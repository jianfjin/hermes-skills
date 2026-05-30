# Three-Seat Focused Code Review Pattern

After subagent implementation, dispatch 3 council seats for code review.
Each reviews from a different lens with a structured verdict.

## Seat Assignments

| Seat | Model | Lens | Review Focus |
|------|-------|------|-------------|
| Linus (Arch) | deepseek-v4-pro | System architecture | Design patterns, dependencies, complexity |
| Guido (CLA) | kimi-k2.6 | Python language design | API signatures, type hints, readability, SQL injection |
| Dijkstra (CSO) | kimi-k2.6 | Correctness | Concurrency, edge cases, failure modes |

## Review Brief Structure

1. **Context**: What was built, changed files
2. **New files**: List each with description
3. **Modified files**: List each with description
4. **Per-seat prompts**: Questions targeting their expertise
5. **Output format**: `[Seat/Role] analysis + APPROVE/REJECT/CONDITIONAL_APPROVE`

## Worked Example (2026-05-24: PG persistence + Kanban)

Common blockers found by all three seats:
- Tests using `pytest.mark.asyncio(coro)` w/o parentheses — never executed
- `asyncpg` in sync methods via `new_event_loop()` — production crash risk
- `asyncpg` missing from `requirements.txt`
- `verify_chain()` skipped first row, no session filter
- UnboundLocalError from uninitialized variable in finally block
- `time.time()` float sent to PostgreSQL TIMESTAMPTZ column

## Pitfalls

- Profile named `jobs` conflicts with bash builtin. Use `hermes --profile steve` instead.
- Kimi-k2.6 agents (Dijkstra, Guido) are bottlenecks — launch first.
- Require a structured verdict (APPROVE/REJECT/CONDITIONAL_APPROVE) from each seat.
- Items flagged by all three seats are highest-priority fixes.
- Re-review if any seat issued REJECT.
