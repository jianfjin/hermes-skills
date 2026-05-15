# Debate Brief Template

Use this structure when writing a debate brief for the Inner Circle. The brief should be self-contained — agents must be able to reason from it without external references.

## Template

```markdown
# [TOPIC] 议会辩论 Brief

## 背景

[2-3 sentences: who we are, what decision we're facing, why it matters]

## 核心信息

[Bullet points of essential facts. Pre-digested from external sources (proposals, documents, specs).
NO URLs. NO references to external files agents can't access.]

## 关键角色和关系

[Who is who. If this involves external parties (clients, partners, regulators), name them and their role.]

## 任务分解 (if applicable)

[Break down the work into numbered tasks with owners and deadlines]

## 交付物 (if applicable)

| 编号 | 名称 | 负责人 | 截止 | 类型 |
|------|------|--------|------|------|

## 上游依赖

[What we need from others, in what format, by when]

## 下游输出

[What we provide to others, in what interface]

## 核心问题

[Numbered list of questions each agent should address from their role perspective.
Frame these as role-specific prompts, not generic questions.]

1. [Question for first-principles analysis]
2. [Question for architecture]
3. [Question for risk/cost audit]
4. [Question for API/interface design]
5. [Question for algorithmic correctness]
6. [Question for infrastructure]
7. [Question for product/UX]
8. [Question for implementation pragmatism]
```

## Anti-patterns (DO NOT include)

- Raw URLs (agents will try to browse them — wastes 2-3 min per agent)
- "See attached document" references
- Full architecture descriptions the agents can't verify
- Benchmark numbers without context
- "The CTO thinks X" — let agents form independent opinions

## Example: SCAILED WP4 Brief

The brief at `/tmp/scailed_debate_brief.txt` used during the 2026-05-13 9-member debate followed this template exactly. Key stats:
- 3,050 characters (fits in all agent context windows comfortably)
- 8 role-specific questions
- Pre-digested from a 2MB PDF (214 pages)
- Zero agent browser/API call attempts
- All 8 agents produced meaningful output in 34-100 seconds
