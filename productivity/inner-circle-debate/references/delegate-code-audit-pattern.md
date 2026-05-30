# Delegate Code Audit Pattern

When `delegate_task` subagents produce production code, a focused 4-seat council audit catches implementation-level issues (concurrency bugs, error handling gaps, brittle patterns) that the subagents miss. This is distinct from the Plan Review debate (which audits before code is written) — this audits code that already exists.

**Seats**: Xuefeng (CSA, cost/risk) + Linus (Arch, performance) + Guido (CLA, readability/API) + Dijkstra (CSO, correctness)

**When to use**: After any `delegate_task` that produced >200 LOC of production code, especially async code, caching logic, or API integrations.

## Pattern (battle-tested 2026-05-23, pharm_platform)

### Step 1: Write per-seat audit briefs

Each auditor gets the same shared context brief + a domain-specific question. Write brief files to `/tmp/<topic>_audit/audit_<seat>.txt` using `execute_code` (avoids shell quoting issues).

Shared brief: project path, branch, commit range, what was built, test results. Keep it self-contained — no URLs, no external references (agents will try to verify independently and waste time).

Per-seat focus questions:
- **Xuefeng**: "Audit for COST + RISK + PRAGMATISM. What breaks first in production? Rank top 5 risks."
- **Linus**: "Audit for ARCHITECTURE + PERFORMANCE. Circular deps? Blocking in async? Be brutal."
- **Guido**: "Audit for API DESIGN + READABILITY. Type hints complete? Pythonic? Bare excepts?"
- **Dijkstra**: "Audit for CORRECTNESS + EDGE CASES. Race conditions? TOCTOU? Silently swallowed errors?"

### Step 2: Launch in parallel

```bash
# Launch kimi agents FIRST (slowest)
guido chat -q "$(cat /tmp/<topic>_audit/audit_guido.txt)" &  # kimi-k2.6
dijkstra chat -q "$(cat /tmp/<topic>_audit/audit_dijkstra.txt)" &  # kimi-k2.6

# Then deepseek agents
xuefeng chat -q "$(cat /tmp/<topic>_audit/audit_xuefeng.txt)" &  # flash, ~40s
linus chat -q "$(cat /tmp/<topic>_audit/audit_linus.txt)" &  # pro, ~60-100s
```

Use `terminal(background=True, notify_on_complete=True, timeout=600)` from within a Hermes session.

### Step 3: Wait with staggered polling

- deepseek-v4-flash (Xuefeng): completes ~40s
- deepseek-v4-pro (Linus): completes ~60-100s
- kimi-k2.6 (Guido, Dijkstra): completes ~2-12 min (may hit API timeouts)

If kimi agents exceed 200s with no output preview, skip them. 3/4 auditors usually establish consensus.

### Step 4: Synthesize audit report

Structure:
1. Severity tiers (CRITICAL / HIGH / MEDIUM / LOW)
2. Per-finding: auditor, file:line, description, fix
3. "What's NOT broken" section — credit good patterns found
4. Fix priority matrix (P0: before next demo, P1: before production, P2: next iteration)
5. Estimated fix effort

### Step 5: Fix + re-verify

Execute fixes (ideally via another `delegate_task`), run full test suite, commit.

**Worked example**: `pharm_platform/docs/records/2026-05-23-code-audit.md` — 1500 LOC audited, 20 findings (5 CRITICAL, 6 HIGH, 5 MEDIUM, 6 LOW), 4/4 auditors confirmed structural soundness, all CRITICAL fixed in one pass.

**Key insight**: Auditors find different classes of bugs than tests. The 84 passing tests did not catch the TOCTOU race, the set-ordering bug, or the Chinese keyword gap. Auditors caught all three.
