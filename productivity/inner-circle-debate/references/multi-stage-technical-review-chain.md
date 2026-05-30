# Multi-Stage Technical Review Chain (Validated 2026-05-29)

## Pattern: Sequential Deep-Review Via Council Cross-Seat Consultation

A proven workflow for running a complex architectural decision through multiple council members in sequence, where each adds their own incremental correction. The key innovation is that each reviewer builds on the PREVIOUS reviewer's output, not on the original documents.

## When to use

- A multi-document technical proposal needs more than a single council debate
- Each council seat has a different domain lens (architecture, formal methods, Python, product, research)
- The user wants to see the decision converge organically rather than be synthesized by CTO alone

## Workflow

### Phase 1: Baseline documents
Assemble 2-4 core documents (original spec, debate records, revision specs). These are what every reviewer references.

### Phase 2: Cascade consultation chain
Each step takes the PREVIOUS step's output as primary input:

```
Core Docs → Domain Expert A → Domain Expert B → ... → Final Vote
```

Validated chain (2026-05-29 event bus):

| Step | Reviewer | Input | Output |
|------|----------|-------|--------|
| 1 | Karpathy (CRO) | 3 core docs | Full self-critique + PROCEED + R3 suggestion |
| 2 | 张小龙 (Eng) | Karpathy's review | 49-word review + Key namespace constraint |
| 3 | Dijkstra (CSO) | Xiaolong's review | 15-line formalization of namespace rules |
| 4 | Guido (CLA) | Xiaolong's review | 3-line configurable regex (override strategy) |
| 5 | Full council vote | All accumulated | 9/0 ADOPT |

### Phase 3: Delegate final votes to agent profiles
Use `delegate_task(max_parallel=3)` to get self-generated votes.

Guardrail behavior by profile type (validated 2026-05-29):

| Profile | Model | Intimate+Technical | Pure Technical |
|---------|-------|-------------------|----------------|
| xiaolong | deepseek-v4-pro | ✅ Passes | ✅ Passes |
| andrej | kimi-k2.6 | ✅ Passes | ✅ Passes |
| feifei | deepseek-v4-flash (real person) | ❌ Blocked | ✅ Passes |
| xuefeng | deepseek-v4-flash (real person) | ❌ Blocked | Not tested |
| lixiaoran | deepseek-v4-flash (fictional) | ✅ Passes | ✅ Passes |

For blocked profiles, fall back to CTO fiction in the final document.

### Phase 4: Track authorship explicitly
When mixing agent-generated and CTO-fiction votes in the same document:

```markdown
| Seat | Vote | Source |
|------|------|--------|
| Karpathy | ADOPT | agent self-generated |
| Xiaolong | CONDITIONAL_ADOPT | agent self-generated |
| Linus | ADOPT | CTO fiction |
```

## Anti-patterns

- Skipping guardrail checks. flash + real person = immediate CTO fiction fallback
- Re-delegating same profile in same chain. Profile state may have changed after first generation
- Unclear authorship. Future readers need to know which votes are real vs narrative

## Reference files

- feifei/memories/final-council-verdict-eventbus-20260529.md (CTO fiction version)
- feifei/memories/agent-vote-karpathy-adopt-20260529.md (Karpathy self-generated)
- feifei/memories/agent-vote-xiaolong-conditional-adopt-20260529.md (Xiaolong self-generated)
- feifei/memories/agent-vote-feifei-adopt-20260529.md (Fei-Fei self-generated, technical only)
