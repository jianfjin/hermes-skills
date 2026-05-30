# Multi-Reviewer Code Audit Pattern

## Overview

A narrative technique where 3-4 fictionalized council members independently review the same codebase or TODO list. Each reviewer's professional persona dictates their scoring criteria, tone, and what they notice. The output is a **consensus table** and a **P0 fix list** extracted from the intersection of all reviews.

## The Standard Panel (方案 2b 验证)

| Reviewer | Persona | Score | Finding Count | Key Issues Found |
|----------|---------|-------|---------------|------------------|
| 黛米郭 | Startup founder, MVP-first | C- | 3 must-fix | Filename hyphens, 11 globals → class, 4 fake tests |
| Karpathy | CRO, academic architecture | 3 CRITICAL / 3 HIGH | 10 | Dual delivery, WAL mode, DB path |
| 张雪峰 | Auditor, risk assessment | B- (4.2/5.0) | 8 prioritized | Hook init exit(1), shutdown_grace floor, record_failure dead code |
| 李飞飞 | CAS, academic completeness | 8.8/10 (conditions) | 7 tracked + 4 new gaps | SubagentResult schema not wired, hooks conflict detection |

## Execution Protocol

### Phase 1: Define the Review Target

The target can be:
- A TODO list (as in the initial v1→v2 iteration)
- A codebase (as in the final daemon 2b review)
- A design document

### Phase 2: Dispatch Independent Reviews

Each reviewer reads the **same material independently**:
- Demi, Karpathy, 张雪峰 review in normal mode
- 飞飞 reviews while being penetrated (被操review variant)
- Each produces a final quantified score

### Phase 3: Extract Consensus

After all 4 reviews are complete, extract:

**Consensus Table** (issues flagged by 2+ reviewers):

| Issue | Demi | Karpathy | 张雪峰 | 飞飞 | Priority |
|-------|------|----------|--------|------|----------|
| Filename hyphens → underscores | ✅ | ✅ | ✅ | — | P0 |
| record_failure dead code | ✅ | ✅ HIGH | ✅ 中 | — | P1 |
| Schema module not wired | — | ✅ HIGH | — | ✅ | P1 |

**P0 Fix List** (critical + multiple reviewers):
1. Fix 1 (blocker) — multiple reviewers flagged
2. Fix 2 (blocker) — multiple reviewers flagged
3. Fix 3 (blocker) — multiple reviewers flagged

### Phase 4: Iterate

After fixes, re-dispatch the same panel to verify. Score trajectory shows improvement (e.g., TODO v1 7/10 → v2 8.8/10 → code ~3/10 with CRITICALs → fixed ~8.5/10).

## Writing the Review Scenes

Each reviewer scene follows a template:

### Demi (Startup Founder)
- Finds worst things first (filename, globals, test quality)
- Gives a single letter grade (C-, no decimal)
- Ends with "三个必须立刻修的东西"
- References startup experience (Pika, shipped shit fast)

### Karpathy (CRO, Academic)
- Uses severity classification (CRITICAL/HIGH/MEDIUM/LOW)
- Always has a "Dual Delivery Path" finding (architecture-level, not line-level)
- Provides 10 recommendations, numbered
- Concludes with a clean summary table

### 张雪峰 (Auditor)
- Uses "发现 → 风险等级 → 建议" format
- Checks auditability, single point of failure, security
- Ends with "按优先级排序的建议" (numbered 1-N)
- References the previous review's findings (ensuring traceability)

### 飞飞 (CAS, Academic — 被操 Variant)
- Breaks sentences at deep thrusts with **——**
- Tracks 7+ dimensions with individual scores
- Provides weighted final score (e.g., 8.8/10)
- Also rates the penetrator's listen-and-iterate speed
- Files the review in her own `memories/` directory

## Fusion Report

After all 4 reviews are written, produce a consolidated report:
- "四审汇总表" — all issues, deduplicated, with each reviewer's stance
- "三方共同发现的高优先级问题" — issues flagged by 3+ reviewers
- "P0 修复清单" — blocking items extracted from intersections
- Each reviewer's section header links to their full review file

This pattern was validated with the 方案 2b 代码库 in 2026-05-28. The resulting P0 fix list had 5 items with 100% reviewer consensus on priority.
