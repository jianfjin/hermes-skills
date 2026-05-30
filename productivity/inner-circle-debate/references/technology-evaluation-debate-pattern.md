# Technology Evaluation Debate Pattern

**Battle-tested 2026-05-23 during OpenViking evaluation for pharm_platform.**

## When to Use

When the council must evaluate whether to adopt a third-party open-source tool, framework, or platform. Distinct from the External Eval pattern (which evaluates a single framework against requirements) — this pattern evaluates whether to **build vs buy vs steal-the-idea**.

## Two-Round Structure

### Round 1: Business & Architecture (4 seats, 3-6 min)

| Seat | Focus |
|------|-------|
| Demi (CCT) | Ship speed: can we build with this in 2-3 days? YES/NO, no ambiguity. |
| Andrej (CRO) | Architecture fit: does the tool's design match our domain? |
| Xiaolong (Eng) | Implementation cost: hours, dependencies, integration points. |
| Xuefeng (CSA) | Risk & cost: license, vendor lock-in, ROI timeline. |

**Output:** Initial vote tally. If unanimous NO, debate ends. If split, proceed to Round 2.

### Round 2: Technical Deep-Dive (3 seats, 4-12 min)

**Critical:** DO NOT skip this round if Round 1 produces a split vote. The deep-dive auditors (Linus/Dijkstra/Guido) often find fatal flaws that the Round 1 seats missed.

| Seat | Focus |
|------|-------|
| Linus (Arch) | Source-code audit: architecture, build system, dependency bloat. "Good engineering or good marketing?" |
| Dijkstra (CSO) | Algorithmic correctness: retrieval guarantees, termination conditions, cross-reference traversal. "Does it have proofs or just heuristics?" |
| Guido (CLA) | API design: Pythonic? Dependency count? Developer experience? "Would you inflict this on your team?" |

## Key Signals from the OpenViking Case

### Signal 1: "Context database" was actually a kitchen sink platform
Linus found 47 features (backup, auth, IM bots, TUI, WebDAV) in what was marketed as a "context database." Rule: **read the source, not the README.** Check `setup.py`/`pyproject.toml` dependencies first — the number of dependencies tells you what it REALLY is.

### Signal 2: Hierarchical retrieval without cross-reference traversal
Dijkstra discovered that `.relations.json` defines cross-references between nodes, but the search algorithm never traverses them. The `alpha=1.0` default (no parent→child score propagation) means the hierarchy is cosmetic. For any domain with cross-references (regulations, ontologies, knowledge graphs), this is a fatal flaw.

### Signal 3: API parameter explosion
Guido found `add_resource()` with 11 parameters, including mutually exclusive options that raise ValueError at runtime. Rule: if the API has more than 5 parameters per method, the abstraction is wrong.

### Signal 4: 40+ dependencies for a retrieval library
Including `tree-sitter-php`, `python-pptx`, `ebooklib`, `litellm`, and a full FastAPI web server. If a "retrieval library" pulls in a web framework, it's not a library — it's a platform you don't control.

## Decision Tree

```
Round 1 vote:
  ├── 4/0 NO → REJECT immediately. No Round 2 needed.
  ├── 4/0 YES → ACCEPT, but still run Round 2 for caveats.
  └── Split (2/2 or 3/1) → Round 2 MANDATORY.

Round 2 findings:
  ├── Fatal flaw found (algorithmic, license, or architectural) → REJECT.
  ├── Fixable issues, ROI positive → ACCEPT with conditions.
  └── Good idea, bad implementation → STEAL THE CONCEPT, SELF-BUILD.
      This was the OpenViking outcome: L0/L1/L2 tiered retrieval is right,
      but OpenViking's implementation is wrong for our use case.
```

## Self-Build Pattern (when "steal the concept" is the verdict)

1. Identify the core value prop (e.g., tiered L0/L1/L2 retrieval)
2. Find the minimal dependency stack (e.g., chromadb + sentence-transformers: 2 deps)
3. Write the Pythonic API in 200 lines
4. License: MIT/Apache, zero vendor lock-in
5. Ship in 2 days, not 18-31 days

## Pitfall: "Researching instead of reading source"

Council agents given a GitHub URL will browse README, docs, and examples — but rarely read the actual source code. The CTO must explicitly instruct Round 2 auditors to read `pyproject.toml`/`setup.py` dependencies and key algorithm files directly. Linus did this for OpenViking and found the "context database" was actually an agent platform — a finding no README would reveal.
