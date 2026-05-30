# Council Delegation via delegate_task

When the council produces implementation tasks (not just analysis), assign work via
`delegate_task` using each seat's domain expertise.

## Pattern

```
Council debate → task decomposition → delegate_task per task → CTO integrates
```

## When to Delegate vs Launch a Council Profile

| Need | Method | Tools Available |
|------|--------|-----------------|
| Architecture analysis, debate | `terminal("linus chat ...")` | Chat only |
| Implementation, code changes | `delegate_task(goal="...")` | file, terminal, search |
| Code review after implementation | `delegate_task(goal="Review ...")` | file, terminal, search |

## Best Practices

1. Each task must be self-contained on its own files (deletion vs creation can be parallel)
2. Integration step belongs to the CTO, not delegated
3. Do NOT delegate tasks touching the same files in parallel
4. Provide full implementation context (not just "implement this")
5. Verify each subagent completed successfully before proceeding
6. Test coverage expectation: all new code needs tests

## Worked Example (2026-05-24: PG Persistence + Kanban)

```
1. Linus (delegate_task): Delete AGE code
   - git rm graph_age.py, AGE tests, solver async, etc.
   - Outcome: 12 files changed, 800+ lines removed

2. Xiaolong (delegate_task): Create PG repos + kanban
   - New: repositories/, middleware/, dashboard.py, dashboard.html
   - Outcome: 8 new files created

3. CTO (manual): Wire PG persistence into AssessmentService
   - Add _pg_conn(), _pg_write_session(), wire into 3 methods
   - Outcome: 63 lines added to assessment_service.py

4. CTO (manual): Write tests for new code
   - test_repositories.py, test_request_logger.py
   - Outcome: 2 new test files

5. CTO (manual): Update workflow documentation
   - docs/pathfinder-workflow.md + .html
```
