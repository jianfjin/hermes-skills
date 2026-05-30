# Parallel Delegate-Task Code Generation Pattern

**Battle-tested 2026-05-22 — pharm_platform 3-day demo, 1900 LOC in 3 commits**

When implementing a multi-file plan, splitting the work into parallel `delegate_task` subagents is faster than sequential execution or `terminal(background=True)` profile spawning. Subagents can write files, run tests, and validate their own output — fully autonomous.

## When to Use

| Scenario | Use |
|----------|-----|
| 2-3 independent workstreams (different modules) | ✅ Parallel delegate_task |
| Single linear dependency chain | ❌ Sequential |
| Needs council-style debate | ❌ Use terminal(background=True) profiles |
| Just writing boilerplate/config | ❌ Direct write_file |

## Pattern

```python
delegate_task(tasks=[
    {
        "goal": "Write live PubMed + ChEMBL async retrievers...",
        "context": "Read existing protocol from rag.py first. Write pubmed.py (~40 loc) and chembl.py (~35 loc)...",
        "toolsets": ["terminal", "file"]
    },
    {
        "goal": "Create static EHDS articles JSON and drug crosswalks CSV...",
        "context": "Research real EHDS regulation text. Use real ChEMBL IDs...",
        "toolsets": ["terminal", "file", "web"]
    }
])
```

Both subagents run in parallel. The `delegate_task` call blocks until ALL complete. Each subagent returns a summary.

## pharm_platform Results

| Day | Pattern | Subagents | Duration | Output |
|-----|---------|-----------|----------|--------|
| 1 | 2 parallel | retrievers + static data | 3.8 min | 412 LOC, 7 tests |
| 2 | 2 parallel | bridge + RAG/cache | 2.3 min | 1074 LOC, 45 tests |
| 3 | 2 parallel | demo script + demo tests | 3.6 min | 424 LOC, 7 tests |

**Total: 3 commits, ~1900 LOC, 59 tests, <10 minutes wall-clock time.**

## Key Rules

1. **Each subagent gets a self-contained goal.** Include file paths, existing contracts to read, and expected output.
2. **Subagents read existing code first** — specify which files to read in the context.
3. **Subagents run their own tests** — include "Run tests with: cd ... && python3 -m pytest" in the goal.
4. **Avoid cross-subagent dependencies.** Don't have subagent B depend on subagent A's output. Split at module boundaries.
5. **Max 3 subagents per batch** — `delegation.max_concurrent_children` defaults to 3.
6. **Subagents are leaf by default** — they can't re-delegate. For orchestrator chains, set role="orchestrator".

## Anti-Pattern: Context Overload

Do NOT dump the full plan document into each subagent. Give each one ONLY what it needs:
- Which files to read (existing contracts)
- What to create/modify
- What tests to run
- The specific API/format requirements

## Variant: Council-Member Delegation (2026-05-24, battle-tested)

When the council produces a multi-workstream plan (e.g., delete AGE + create PG repos + build kanban), execute it by delegating well-defined workstreams to individual council members via `delegate_task`, then integrating as the CTO.

**Pattern:**

1. **CTO creates the branch** and writes the brief for each workstream.
2. **CTO delegates each workstream** via `delegate_task` — each subagent acts as one council member (e.g., "Linus: delete AGE", "Xiaolong: create PG repos").
3. **Subagents work in parallel** — each reads existing code, writes/modifies files, runs verification.
4. **CTO integrates** — reads all subagent outputs, wires cross-cutting concerns (e.g., session persistence into AssessmentService), commits.

**Key rules:**
- Split by **file boundary**, not by function. Subagent A deletes graph_age.py and cleans imports; Subagent B creates new repository files. If both touch assessment_service.py, one will overwrite the other.
- Each subagent gets **self-contained context**: file paths, existing code to read, exact output expected.
- Each subagent **runs verification** (`python3 -c "import ..."`) before returning.
- The CTO **never delegates integration work** — the wiring across all three workstreams is the CTO's job.

**Battle-tested results (this session):**
- Subagent 1 (Linus): deleted 4 files, modified 8 files, removed AGE — 242s, 27 API calls
- Subagent 2 (Xiaolong): created 8 new files, modified 2 existing files — 126s, 16 API calls
- CTO integration: wired session persistence, verified demo — ~5min
- **Total: ~11 minutes wall-clock for ~20 file changes across 3 workstreams**

**Pitfall: parent must re-read files before editing.** Subagents can modify files the parent previously read. After delegate_task returns, the parent's in-memory views of those files are stale — use `read_file` again before making any patch/write_file calls.

## Pitfall: Subagent Overwrites

If two subagents touch the same file, the slower one wins (last write). Avoid this. The demo/__init__.py collision in Day 3 was harmless because the placeholder was overwritten by the real file. For critical shared files, use sequential execution or explicit coordination.
