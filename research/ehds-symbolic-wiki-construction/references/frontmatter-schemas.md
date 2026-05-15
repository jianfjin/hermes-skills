# Frontmatter Schemas for EHDS Three-Layer Stack

## Index Layer (`ehds_index/`)

One file per Article. Immutable stable_id. No interpretation — only regulation text.

```yaml
---
regulation: "Reg. (EU) 2025/327"
article: 54
title: "Permitted purposes for secondary use — scientific research"
chapter: "V"
stable_id: "EHDS-2025-327-A54"   # NEVER CHANGE THIS
category: "secondary_use"        # taxonomy tag for grouping
date_enacted: "2025-03-11"
---
```

**Required fields:** `regulation`, `article`, `title`, `stable_id`
**Optional but recommended:** `chapter`, `category`, `date_enacted`

## Wiki Layer (`ehds_wiki/`)

Semantic associations, human-readable context, machine-parseable metadata.

```yaml
---
wiki_id: "WIKI-SEC-001"
title: "Secondary Use of Health Data"
regulation: "Reg. (EU) 2025/327"
article: 54
category: "secondary_use"
keywords: ["scientific research", "HDAB approval", "public health", "data reuse", "Annex II"]
index_refs: ["EHDS-2025-327-A54", "EHDS-2025-327-A55", "EHDS-2025-327-A33"]
anchors: ["A54-P1", "A54-P2", "A54-P3", "A54-P4", "A33-P4"]
created: "2026-05-08"
updated: "2026-05-11"
author: "CTO-FengGe"
---
```

**Required fields:** `wiki_id`, `title`, `regulation`, `article`, `category`, `keywords`, `index_refs`, `created`, `updated`
**Optional but recommended:** `anchors`, `author`

### Field Definitions

| Field | Type | Purpose |
|-------|------|---------|
| `wiki_id` | string | Unique wiki identifier (e.g. `WIKI-SEC-001`) |
| `title` | string | Human-readable title |
| `regulation` | string | Source regulation citation |
| `article` | int | Primary article number |
| `category` | string | Taxonomic category |
| `keywords` | list[str] | Searchable tags |
| `index_refs` | list[str] | Stable IDs of referenced Index entries |
| `anchors` | list[str] | Specific paragraph anchors referenced |
| `created` | date | Creation date `YYYY-MM-DD` |
| `updated` | date | Last modification date `YYYY-MM-DD` |
| `author` | string | Responsible party |

## KB Layer (`ehds_kb/`)

Machine-actionable rules. Frontmatter is lightweight — focus is on structured content.

```yaml
---
rule_id: "EHDS-SEC-AUTH-001"
severity: "critical"
article: 54
category: "secondary_use"
type: "heuristic"
---
```

**Recommended fields:** `rule_id`, `severity`, `article`, `category`, `type`

## Anchor ID Convention

Format: `A{article:03d}-P{paragraph}`

Examples:
- Art. 54 Para 2 → `A54-P2`
- Art. 5 Para 1 → `A5-P1`
- Art. 33 Para 6 → `A33-P6`

These appear in:
- Index `## Audit Anchors` section as `[[A54-P2]] :: description`
- Wiki `anchors:` frontmatter list
- Citation resolver input strings like `EHDS-2025-327-A54-P2`
