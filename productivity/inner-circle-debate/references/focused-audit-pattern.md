# Focused Council Audit Pattern

Used when the council needs to audit existing code (not debate a decision).
4-seat subset, domain-focused briefs, parallel launch, P0/P1/P2 priority synthesis.

## When to use this pattern

- Code audit of a feature branch before merge
- External tool/library evaluation (e.g., "should we adopt X?")
- Post-implementation quality review

NOT for: technology selection debates (use full council), product decisions (use Jobs+Musk+Xuefeng).

## Seat selection

| Seat | Domain | Use when |
|------|--------|----------|
| Dijkstra (CSO) | Algorithmic correctness, edge cases, termination proofs | Any code with logic branches |
| Linus (Arch) | Architecture, performance, resource management | Any code touching I/O, databases, concurrency |
| Guido (CLA) | API design, Pythonic quality, readability, dead code | Any Python module with public API |
| Andrej (CRO) | Retrieval quality, embedding strategy, ML architecture | RAG, embeddings, vector search, LLM pipelines |
| Xuefeng (CSA) | Risk, cost, license, dependency audit | External dependencies, build complexity |

**Seat assignment rule:** Match the auditor's domain to the code's domain. Don't ask Guido to audit cache locking (that's Linus). Don't ask Xuefeng to audit API design (that's Guido).

## Brief format

Each auditor gets the SAME shared context brief + ONE domain-specific focus section. The shared brief includes:
- Branch/commit being audited
- File list with line counts
- Architecture overview (1 paragraph)
- Test status

Each focus section is 3-5 bullet points directing the auditor's attention to what matters for their domain.

**Critical:** Include a note about any pre-existing false alarms or known issues so auditors don't waste time on them.

## Launch order

```
1. Launch kimi-k2.6 agents FIRST (Dijkstra, Guido, Andrej) — they're the bottleneck
2. Launch deepseek agents after (Linus, Xuefeng) — they finish faster
3. Wait for all, collect logs, synthesize
```

## Synthesis format

Three-tier priority:
- **P0 (blocking merge):** Data corruption, silent failures, security holes
- **P1 (high):** Performance bugs, architectural issues, missing error handling
- **P2 (medium):** Dead code, style issues, documentation gaps

Include a "What's NOT broken" section — credit where due keeps council morale up.

## P0 false-alarm rule

When an auditor claims "CRITICAL: X is broken", the CTO MUST verify by reading the actual code before accepting the finding. Example from this session: Dijkstra, Andrej, and Linus all claimed L2 lookup uses wrong ID key — code inspection revealed the IDs actually match (both use source_uri). The real bug was subtler (section-scoped L1 URIs vs article-scoped L2 URIs).

**Always cross-check P0 claims against source code before fixing.**
