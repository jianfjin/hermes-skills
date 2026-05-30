# External Tool Evaluation Pattern (Demi-Led, 2026-05-24)

A pattern for evaluating third-party open-source tools by convening a
focused council led by Demi (CCT), then implementing a lightweight
alternative when the full tool is too heavy.

## Pattern

```
1. BRIEF — CTO writes brief with:
   - What the tool does (from README + code structure)
   - Current system architecture (what exists)
   - Specific evaluation questions per seat

2. CONVENE — Demi leads, 3-4 domain-relevant seats:
   - Demi (CCT) — chairs, product fit, ROI
   - Domain-expert seat (Andrej for RAG, Linus for arch, etc.)
   - Domain-expert seat #2 (Fei-Fei for AI quality, etc.)
   - Guido (CLA) — Python integration, dependency chain, license

3. VOTE — Each seat issues: ADOPT / HOLD / REJECT + rationale
   - If unanimous HOLD/REJECT → proceed to Step 4
   - If split → Demi chairs a second round with narrowed questions

4. LIGHTWEIGHT ALTERNATIVE — CTO implements ~200 lines:
   - Replace 3-4GB dependency with pip install (2MB)
   - Implement core protocol (BioChemRetriever)
   - Document limitations clearly in the design doc
   - Tests verify with mocks, no external services needed

5. REVIEW — Guido + Demi review the implementation
   - Same CONDITIONAL_APPROVE / REJECT format
   - Must-fix list from both reviewers must be resolved
```

## Worked Example: RAG-Anything (2026-05-24)

| Step | Action | Outcome |
|------|--------|---------|
| 1 | CTO cloned RAG-Anything, read README + code structure | Brief written |
| 2 | Demi + Andrej + Fei-Fei + Guido convened | 4 seats |
| 3 | Vote: 4/4 HOLD | Unanimous |
| 4 | Implemented LocalDocumentRetriever (~200 lines, pypdf 2MB) | pip install pypdf, ChromaDB |
| 5 | Demi + Guido review | CONDITIONAL_APPROVE both |

## When to use this pattern

- Evaluating a tool that looks promising but has heavy dependencies
- The tool does 20% of what the project needs, with 80% overhead
- A lightweight alternative can be built in < 1 day
- The evaluation involves multiple dimensions (product, ML, architecture, Python)
