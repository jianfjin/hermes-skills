# Enhanced Frontmatter Schema for Paperclip Neuro-Symbolic Nodes

## Design Source: Inner Circle Debate 2026-05-12

Incorporates:
- **Temporal KG** from MemPalace (valid_from/valid_to)
- **Confidence Tagging** from Graphify (EXTRACTED/INFERRED/AMBIGUOUS)
- **Verbatim Commitment** from MemPalace (raw/ immutability)

## Full Enhanced Frontmatter (Wiki Layer)

```yaml
---
# ── Identity (existing) ──
wiki_id: "WIKI-SEC-001"
title: "Secondary Use of Health Data"
stable_id: "EHDS-2025-327-A54"          # Immutable forever
regulation: "Reg. (EU) 2025/327"
article: 54
chapter: "V"
category: "secondary_use"

# ── Temporal (NEW — from MemPalace inspiration) ──
valid_from: "2025-03-11"                # When this rule became effective
valid_to: null                           # null = still in force; set date when superseded
supersedes: ["EHDS-2022-Compromise-A42"] # Prior version(s) this replaces
superseded_by: null                      # Future version that replaces this

# ── Confidence (NEW — from Graphify inspiration) ──
confidence: high                         # high | medium | low
confidence_basis: "extracted"            # extracted | inferred | ambiguous
confidence_note: "Regulation text explicitly states obligation"  # Optional human rationale

# ── Audit Trail (existing, enhanced) ──
keywords: ["scientific research", "HDAB approval", "secondary use"]
index_refs: ["EHDS-2025-327-A54", "EHDS-2025-327-A55"]
anchors: ["A54-P1", "A54-P2"]
created: "2026-05-08"
updated: "2026-05-12"
author: "CTO-FengGe"
contested: false
contradictions: []
sources: ["raw/regulations/EHDS-Reg-2025-327.md"]
---
```

## Field Reference

| Field | Type | Required | Source | Description |
|-------|------|----------|--------|-------------|
| `valid_from` | ISO date | YES | MemPalace | Date the rule text took legal effect |
| `valid_to` | ISO date or null | YES | MemPalace | null = currently in force; date = end of validity |
| `supersedes` | list of stable_id | NO | MemPalace | Prior version(s) this node replaces |
| `superseded_by` | stable_id or null | NO | MemPalace | Future version that replaces this node |
| `confidence` | high/medium/low | YES | Graphify | How well-supported the claims are |
| `confidence_basis` | extracted/inferred/ambiguous | YES | Graphify | What the confidence rating is based on |
| `confidence_note` | string | NO | Graphify | Human-readable justification |

## Temporal Chain Example

```
EHDS-2022-Compromise-A42
  └── superseded_by → EHDS-2024-Draft-A54 (valid_from: 2024-03-01, valid_to: 2025-03-10)
       └── superseded_by → EHDS-2025-327-A54 (valid_from: 2025-03-11, valid_to: null)
```

## Confidence Decision Matrix

| Situation | confidence_basis | confidence |
|-----------|-----------------|------------|
| Explicitly stated in primary regulation text | extracted | high |
| Clearly implied by regulation + official guidance | inferred | medium |
| Reasonable deduction from context, no official confirmation | inferred | low |
| Cross-referenced but interpretation disputed | ambiguous | low |
| Single-source claim, no corroboration | ambiguous | low |

## Migration: Adding to Existing Nodes

For existing Wiki nodes without temporal/confidence fields, add defaults:

```yaml
valid_from: "2025-01-01"     # Conservative: assume EHDS applicability start
valid_to: null                # Assume still in force unless known otherwise
confidence: medium            # Default until reviewed
confidence_basis: "inferred"  # Default until explicitly tagged
```

## Lint Rules

- Any node with `valid_to` in the past must have `superseded_by` set
- Any node with `supersedes` must have `valid_from` > the superseded node's `valid_from`
- `confidence: low` + `confidence_basis: ambiguous` → flag for human review
- Nodes with `valid_to: null` for >2 years without update → flag for staleness check
