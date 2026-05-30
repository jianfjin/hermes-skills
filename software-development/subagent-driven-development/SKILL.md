---
name: subagent-driven-development
description: "Execute plans via delegate_task subagents (2-stage review)."
version: 1.1.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, subagent, implementation, workflow, parallel]
    related_skills: [writing-plans, requesting-code-review, test-driven-development]
---

# Subagent-Driven Development

## Overview

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

## When to Use

Use this skill when:
- You have an implementation plan (from writing-plans skill or user requirements)
- Tasks are mostly independent
- Quality and spec compliance are important
- You want automated review between tasks

**vs. manual execution:**
- Fresh context per task (no confusion from accumulated state)
- Automated review process catches issues early
- Consistent quality checks across all tasks
- Subagents can ask questions before starting work

## The Process

### 1. Read and Parse Plan

Read the plan file. Extract ALL tasks with their full text and context upfront. Create a todo list:

```python
# Read the plan
read_file("docs/plans/feature-plan.md")

# Create todo list with all tasks
todo([
    {"id": "task-1", "content": "Create User model with email field", "status": "pending"},
    {"id": "task-2", "content": "Add password hashing utility", "status": "pending"},
    {"id": "task-3", "content": "Create login endpoint", "status": "pending"},
])
```

**Key:** Read the plan ONCE. Extract everything. Don't make subagents read the plan file — provide the full task text directly in context.

### 2. Per-Task Workflow

For EACH task in the plan:

#### Step 1: Dispatch Implementer Subagent

Use `delegate_task` with complete context:

```python
delegate_task(
    goal="Implement Task 1: Create User model with email and password_hash fields",
    context="""
    TASK FROM PLAN:
    - Create: src/models/user.py
    - Add User class with email (str) and password_hash (str) fields
    - Use bcrypt for password hashing
    - Include __repr__ for debugging

    FOLLOW TDD:
    1. Write failing test in tests/models/test_user.py
    2. Run: pytest tests/models/test_user.py -v (verify FAIL)
    3. Write minimal implementation
    4. Run: pytest tests/models/test_user.py -v (verify PASS)
    5. Run: pytest tests/ -q (verify no regressions)
    6. Commit: git add -A && git commit -m "feat: add User model with password hashing"

    PROJECT CONTEXT:
    - Python 3.11, Flask app in src/app.py
    - Existing models in src/models/
    - Tests use pytest, run from project root
    - bcrypt already in requirements.txt
    """,
    toolsets=['terminal', 'file']
)
```

#### Step 2: Dispatch Spec Compliance Reviewer

After the implementer completes, verify against the original spec:

```python
delegate_task(
    goal="Review if implementation matches the spec from the plan",
    context="""
    ORIGINAL TASK SPEC:
    - Create src/models/user.py with User class
    - Fields: email (str), password_hash (str)
    - Use bcrypt for password hashing
    - Include __repr__

    CHECK:
    - [ ] All requirements from spec implemented?
    - [ ] File paths match spec?
    - [ ] Function signatures match spec?
    - [ ] Behavior matches expected?
    - [ ] Nothing extra added (no scope creep)?

    OUTPUT: PASS or list of specific spec gaps to fix.
    """,
    toolsets=['file']
)
```

**If spec issues found:** Fix gaps, then re-run spec review. Continue only when spec-compliant.

#### Step 3: Dispatch Code Quality Reviewer

After spec compliance passes:

```python
delegate_task(
    goal="Review code quality for Task 1 implementation",
    context="""
    FILES TO REVIEW:
    - src/models/user.py
    - tests/models/test_user.py

    CHECK:
    - [ ] Follows project conventions and style?
    - [ ] Proper error handling?
    - [ ] Clear variable/function names?
    - [ ] Adequate test coverage?
    - [ ] No obvious bugs or missed edge cases?
    - [ ] No security issues?

    OUTPUT FORMAT:
    - Critical Issues: [must fix before proceeding]
    - Important Issues: [should fix]
    - Minor Issues: [optional]
    - Verdict: APPROVED or REQUEST_CHANGES
    """,
    toolsets=['file']
)
```

**If quality issues found:** Fix issues, re-review. Continue only when approved.

#### Step 4: Mark Complete

```python
todo([{"id": "task-1", "content": "Create User model with email field", "status": "completed"}], merge=True)
```

### 3. Final Review

After ALL tasks are complete, dispatch a final integration reviewer:

```python
delegate_task(
    goal="Review the entire implementation for consistency and integration issues",
    context="""
    All tasks from the plan are complete. Review the full implementation:
    - Do all components work together?
    - Any inconsistencies between tasks?
    - All tests passing?
    - Ready for merge?
    """,
    toolsets=['terminal', 'file']
)
```

### 4. Verify and Commit

```bash
# Run full test suite
pytest tests/ -q

# Review all changes
git diff --stat

# Final commit if needed
git add -A && git commit -m "feat: complete [feature name] implementation"
```

## Task Granularity

**Each task = 2-5 minutes of focused work.**

**Too big:**
- "Implement user authentication system"

**Right size:**
- "Create User model with email and password fields"
- "Add password hashing function"
- "Create login endpoint"
- "Add JWT token generation"
- "Create registration endpoint"

## Parallel Subagent Dispatch by File Boundary

When tasks have non-overlapping file domains, dispatch them in **parallel** via simultaneous `delegate_task` calls:

**Concurrency limit:** The system enforces `max_concurrent_children=3` (configurable in `~/.hermes/hermes-agent/config.yaml` under `delegation.max_concurrent_children`). If you have 4+ tasks, split into batches of 3 — the second batch starts after the first batch's promises resolve.

```python
# Batch 1: 3 tasks in parallel
tasks_1 = delegate_task(tasks=[task1, task2, task3])

# Batch 2: sequential after batch 1
tasks_2 = delegate_task(tasks=[task4, task5])
```

```python
delegate_task(goal="Delete all AGE code", context="...", toolsets=['terminal','file','search'])
delegate_task(goal="Create new repo layer + dashboard", context="...", toolsets=['terminal','file','search'])
```

**Rules for parallel dispatch:**
- Tasks MUST touch **different files** — no overlap whatsoever
- One task creates files, another deletes files = safe
- Two tasks modifying the same file = DO NOT parallelize
- After both complete, the parent session does **integration wiring**
- Verify no conflicts: `git diff --name-only` after both complete

**When to parallelize vs serialize:**
| Pattern | When | Example |
|---------|------|---------|
| Parallel by file boundary | Files are independent | One agent deletes, another creates |
| Serial (dependency chain) | Task B depends on Task A | Schema first, then code that uses it |
| Serial (same file edits) | Both tasks modify same file | Both add routes to api/main.py |

**After parallel dispatch, the PARENT session always does integration wiring:**
```python
# Phase 1: Dispatch parallel subagents (touch different files)
delegate_task(goal="Delete AGE code", ...)     # removes files, cleans imports
delegate_task(goal="Create repos + dashboard", ...)  # creates new files

# Phase 2: WAIT for both to complete (via notify_on_complete + poll)

# Phase 3: PARENT integrates — this is critical and non-delegable
# The parent session wires the new components into existing service code
# because integration touches BOTH sets of files (the ones A created and B modified)
patch("assessment_service.py", import repos + add PG write hooks)
```

**The parent must own integration because:**
- Integration code lives at the BOUNDARY between parallel workstreams
- Subagent A doesn't know what B created; subagent B doesn't know what A deleted
- Only the parent has the full picture of both workstreams
- Integration is typically <50 lines, not worth a subagent

## Docs-First Workflow

This user requires **docs first, review second, code third**:

1. Write documentation (design doc, spec, architecture overview)
2. Have one or more agents review the docs
3. Only AFTER docs review passes, write code

**Do NOT:** write code before docs, skip review, or treat docs as an afterthought.

## Pitfalls

### Tests That Don't Actually Execute

```python
# WRONG — does nothing, test always passes
def test_foo():
    pytest.mark.asyncio(some_coro())  # no `await`, no async def

# RIGHT — actually executes
@pytest.mark.asyncio
async def test_foo():
    result = await some_coro()
    assert result == expected
```

Always verify tests execute before declaring them done:
```bash
python3 -m unittest tests/test_file.py -v
python3 -c "import asyncio; asyncio.run(test_func())"
```

## Red Flags — Never Do These

- Start implementation without a plan
- Skip reviews (spec compliance OR code quality)
- Proceed with unfixed critical/important issues
- Dispatch multiple implementation subagents for tasks that touch the same files
- Make subagent read the plan file (provide full text in context instead)
- Skip scene-setting context (subagent needs to understand where the task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance
- Skip review loops (reviewer found issues → implementer fixes → review again)
- Let implementer self-review replace actual review (both are needed)
- **Start code quality review before spec compliance is PASS** (wrong order)
- Move to next task while either review has open issues
- **Skip writing tests** — all new code must have tests. The user will ask "测试有没有写？" if they're missing. Tests are NOT optional.

## Multi-Lens Parallel Code Review Pattern

**Validated:** 2026-05-28 — daemon 2b implementation (3 concurrent reviewers: Demi/founder, Karpathy/CRO, 张雪峰/auditor)

When the user wants multiple independent perspectives on the same codebase, dispatch **parallel** `delegate_task` calls with distinct reviewer lenses. Each lens catches a different class of defect.

### Available Lenses

| Lens | Character | Catches | Common findings |
|------|-----------|---------|-----------------|
| **Startup Founder** | Demi Guo | Overengineering, scope creep, wrong priorities | MVP too fat, fake tests, dead code, premature optimization |
| **CRO / Architect** | Andrej Karpathy | Design flaws, concurrency bugs, dependency gaps | Dual delivery paths, missing WAL mode, DB path inconsistencies, design-level anti-patterns |
| **Auditor** | 张雪峰 | Observability gaps, single points of failure, security | No log rotation, hook init exit(1), no traceback, missing idempotency |
| **Academic / Systems** | Fei-Fei Li | Schema completeness, non-functional requirements, testing coverage | Missing type contracts, gaps against spec, underestimated complexity |
| **Kernel / Infrastructure** | Linus Torvalds | Low-level correctness, resource leaks, error handling | Missing edge cases, inconsistent error propagation |
| **Formal / Correctness** | Edsger Dijkstra | Logic errors, concurrency proofs, type safety | Race conditions, unproven termination, type mismatches |

### How to Dispatch

```python
# Read the codebase first
read_file("scripts/daemon-2b.py")
read_file("scripts/daemon-2b-dlq.py")

# Dispatch 3 concurrent reviewers (max_concurrent_children=3)
delegate_task(
    goal="Demi Guo: startup founder review. Is this MVP-sized? What's unnecessary?",
    context="Full codebase contents + your lens",
    toolsets=['terminal', 'file']
)
delegate_task(
    goal="Andrej Karpathy: CRO architecture review. Design flaws? Concurrency?",
    context="Full codebase contents + your lens", 
    toolsets=['terminal', 'file']
)
delegate_task(
    goal="张雪峰: auditor review. Observability? Single points of failure? Security?",
    context="Full codebase contents + your lens",
    toolsets=['terminal', 'file']
)
```

### What Each Lens Typically Finds

From the validated session (daemon 2b, 3 reviewers, 11 files, ~3000 lines):

| Defect Class | Founder | CRO | Auditor | Example finding |
|-------------|---------|-----|---------|-----------------|
| Architecture | No | Yes | No | Dual delivery path (callback + poll) |
| Concurrency | No | Yes | No | Missing WAL mode for SQLite |
| MVP scope | Yes | No | No | "28 tasks → real MVP is 6" |
| Dead code | Yes | Yes | Yes | record_failure() doesn't record |
| Observability | No | No | Yes | No traceback in exception handler |
| Single point of failure | No | No | Yes | hook init failure = exit(1) |
| Fake tests | Yes | No | Yes | test_sighup_handler_registered mocks nothing |
| File naming | Yes | Yes | Yes | Hyphenated filenames break Python import |
| Pornographic comments | No | Yes | No | Sexually explicit text in docstrings |

### Consolidation

After all 3 reviewers complete, produce a consolidated report:

1. **Cross-reference findings** — which issues multiple reviewers flagged (P0 priority)
2. **Lens-unique findings** — issues only one reviewer caught (still valid, lower priority)
3. **Actionable fix list** — prioritized by severity and recurrence across lenses

Save the consolidated report to the project directory. Then dispatch fix subagents per issue cluster.

### When to Use Which Lenses

| Review target | Recommended lenses |
|---------------|-------------------|
| MVP / prototype | Founder + Architect |
| Production deployment | Architect + Auditor |
| Security-sensitive | Auditor + Architect |
| Distributed system | Architect + Formal |
| Existing code refactor | Founder + Kernel |
| Full lifecycle | Founder + Architect + Auditor (minimum) |

## Council Delegation Pattern

When task domain matches a specific council seat (e.g., Linus for architecture, Xiaolong for engineering), use `delegate_task` with their profile persona embedded in the goal:

```python
# Linus (architecture): AGE removal, code cleanup
delegate_task(
    goal="Delete all Apache AGE related code from the project",
    context="...detailed context...",
    toolsets=['terminal', 'file', 'search']
)

# Xiaolong (engineering): new repository layer, dashboards
delegate_task(
    goal="Create PostgreSQL repository layer and Kanban dashboard",
    context="...detailed context...",
    toolsets=['terminal', 'file', 'search']
)
```

**Key differences from launching council profiles via terminal:**
- `delegate_task` creates an isolated subagent that can run file operations — council profiles via `terminal` can only chat
- The subagent has access to tools (file, search, terminal) — council profiles don't
- Use `delegate_task` for implementation work, use `terminal("profile chat ...")` for analysis/opinion

**When to use each:**
| Need | Method |
|------|--------|
| Architecture analysis, debate | `terminal("linus chat ...")` — council profile |
| Implementation, code changes | `delegate_task(goal="...")` — subagent |
| Code review after implementation | `delegate_task(goal="Review ...")` — subagent or council profile |

## Handling Issues

### If Subagent Asks Questions

- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

### If Reviewer Finds Issues

- Implementer subagent (or a new one) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

### If Subagent Fails a Task

- Dispatch a new fix subagent with specific instructions about what went wrong
- Don't try to fix manually in the controller session (context pollution)

## Efficiency Notes

**Why fresh subagent per task:**
- Prevents context pollution from accumulated state
- Each subagent gets clean, focused context
- No confusion from prior tasks' code or reasoning

**Why two-stage review:**
- Spec review catches under/over-building early
- Quality review ensures the implementation is well-built
- Catches issues before they compound across tasks

**Cost trade-off:**
- More subagent invocations (implementer + 2 reviewers per task)
- But catches issues early (cheaper than debugging compounded problems later)

## Integration with Other Skills

### With writing-plans

This skill EXECUTES plans created by the writing-plans skill:
1. User requirements → writing-plans → implementation plan
2. Implementation plan → subagent-driven-development → working code

### With test-driven-development

Implementer subagents should follow TDD:
1. Write failing test first
2. Implement minimal code
3. Verify test passes
4. Commit

Include TDD instructions in every implementer context.

### With requesting-code-review

The two-stage review process IS the code review. For final integration review, use the requesting-code-review skill's review dimensions.

### With systematic-debugging

If a subagent encounters bugs during implementation:
1. Follow systematic-debugging process
2. Find root cause before fixing
3. Write regression test
4. Resume implementation

## Example Workflow

```
[Read plan: docs/plans/auth-feature.md]
[Create todo list with 5 tasks]

--- Task 1: Create User model ---
[Dispatch implementer subagent]
  Implementer: "Should email be unique?"
  You: "Yes, email must be unique"
  Implementer: Implemented, 3/3 tests passing, committed.

[Dispatch spec reviewer]
  Spec reviewer: ✅ PASS — all requirements met

[Dispatch quality reviewer]
  Quality reviewer: ✅ APPROVED — clean code, good tests

[Mark Task 1 complete]

--- Task 2: Password hashing ---
[Dispatch implementer subagent]
  Implementer: No questions, implemented, 5/5 tests passing.

[Dispatch spec reviewer]
  Spec reviewer: ❌ Missing: password strength validation (spec says "min 8 chars")

[Implementer fixes]
  Implementer: Added validation, 7/7 tests passing.

[Dispatch spec reviewer again]
  Spec reviewer: ✅ PASS

[Dispatch quality reviewer]
  Quality reviewer: Important: Magic number 8, extract to constant
  Implementer: Extracted MIN_PASSWORD_LENGTH constant
  Quality reviewer: ✅ APPROVED

[Mark Task 2 complete]

... (continue for all tasks)

[After all tasks: dispatch final integration reviewer]
[Run full test suite: all passing]
[Done!]
```

## Remember

```
Fresh subagent per task
Two-stage review every time
Spec compliance FIRST
Code quality SECOND
Never skip reviews
Catch issues early
```

**Quality is not an accident. It's the result of systematic process.**

## Further reading (load when relevant)

When the orchestration involves significant context usage, long review loops, or complex validation checkpoints, load these references for the specific discipline:

- **`references/context-budget-discipline.md`** — Four-tier context degradation model (PEAK / GOOD / DEGRADING / POOR), read-depth rules that scale with context window size, and early warning signs of silent degradation. Load when a run will clearly consume significant context (multi-phase plans, many subagents, large artifacts).
- **`references/gates-taxonomy.md`** — The four canonical gate types (Pre-flight, Revision, Escalation, Abort) with behavior, recovery, and examples. Load when designing or reviewing any workflow that has validation checkpoints — use the vocabulary explicitly so each gate has defined entry, failure behavior, and resumption rules.

Both references adapted from gsd-build/get-shit-done (MIT © 2025 Lex Christopherson).
