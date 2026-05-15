# 6-Member Inner Circle: Audit → Execute → Review Workflow

Proven pattern from the EHDS three-layer architecture audit session.

## Workflow

```
1. AUDIT PHASE (assign 3 reviewers by expertise)
   ├── Linus (architecture/code quality)      → audit codebase for bugs
   ├── 张小龙 (data/app layer integrity)      → audit data, API, dependencies
   └── Jobs (product/user readiness)          → audit completeness vs promise
   All run in parallel via terminal(background=True)

2. SYNTHESIS (CTO merges findings)
   └── Compile audit report with severity tiers (CRITICAL/HIGH/MEDIUM/LOW)

3. EXECUTION PHASE (assign fixes by expertise)
   ├── Linus tasks: security, architecture, performance (pickle RCE, caching, TF-IDF)
   └── 张小龙 tasks: data quality, API, integration (stable_id, KB rules, frontmatter)
   CTO (峰哥) executes all fixes via patch/write_file

4. CROSS-REVIEW (swap code ownership)
   ├── Linus reviews 张小龙's changes (mcp_server, audit_engine, KB parser)
   └── 张小龙 reviews Linus's changes (embedding, API server, audit_engine)

5. FINAL REVIEW
   └── Jobs reviews the complete deliverable for product readiness

6. REPORT
   └── CTO delivers final summary with: audit findings, fixes applied,
       review findings, remaining gaps, and a product verdict
```

## Role Assignment Rules

| Domain | Audit lead | Fix lead |
|--------|-----------|----------|
| Architecture/security/code quality | Linus | Linus |
| Data quality/API/integration | 张小龙 | 张小龙 |
| Product/completeness/UX | Jobs | N/A (advisory) |
| Synthesis/execution/coordination | 峰哥 (CTO) | 峰哥 (CTO) |

## Example Prompts

### Audit phase prompts

```
linus: "Audit this codebase. Be brutal. Find every bug, security hole,
       architectural flaw. Under 300 words."

xiaolong: "审计数据层和API设计。检查frontmatter完整性、循环依赖、
           参数冗余、输出质量。200字内。"

steve: "Audit product completeness. Does the deliverable match the
        architecture doc's promise? What's the gap? Under 250 words."
```

### Cross-review prompts

```
linus: "Code review. Audit changes made by 张小龙 to files X, Y, Z.
        Check: correctness, edge cases, regressions. Be harsh."

xiaolong: "代码审查。审计Linus对A、B、C文件的改动。检查：安全、
           import路径、数据类型正确性。"
```

## Lessons Learned

- **SOUL.md must be checked before spawning**: cloned profiles start with empty
  SOUL.md templates. Without explicit persona content, the agent speaks in
  the default Hermes tone — audit outputs will be generic.
- **provider-specific quirks must be pre-configured**: kimi-k2.6 needs
  `model.context_length` AND `auxiliary.compression.context_length` overrides
  AND stale `base_url` removal after clone. Test one `chat -q` per profile
  before running the full audit.
- **parallel spawn + wait is faster than sequential**: the 5-agent audit
  completed in ~3.5 minutes vs ~15 minutes sequential.
