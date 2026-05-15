# Data Linkage in EHDS — Domain Knowledge

Extracted from TEHDAS2 M5.4 "Draft Guideline for Data Enrichment" (May 2026)
and cross-referenced with EHDS Regulation (EU) 2025/327.

## Definition (ISO 5127:2017)

> Data linkage is the process of combining datasets "from several sources on one
> topic or data subject" using unique identifiers, probabilistic methods, or a
> combination of techniques.

Source: TEHDAS2 M5.4, Glossary p.47

## The Critical Distinction: Linkage vs. Enrichment

This is the most important concept for EHDS compliance auditing. The two are
frequently confused but have opposite governance models:

| Aspect | Data Linkage | Data Enrichment |
|--------|-------------|-----------------|
| **Timing** | Pre-access (before user gets data) | Post-access (after data permit issued) |
| **Who performs** | HDAB or data holder | Authorised data user within SPE |
| **Legal basis** | Art. 68(1)(b) — must be explicitly requested | No mandatory obligation; Member State discretion |
| **Nature** | Centralised, regulated, formal process | User-driven, analytical, optional |
| **Scope** | Record-level matching across datasets | Adding derived variables or contextual attributes |

## EHDS Legal Basis

**Article 68(1)(b)** — The data access application must specify "whether data
linkage is requested across multiple datasets or data holders."

**Article 66(1)** — Access is only provided to data that is "adequate, relevant
and limited to what is necessary" (data minimisation applies at linkage stage).

## The Trap: Enrichment That Becomes Linkage

> "Where external enrichment involves record-level matching or joining across
> datasets to create person-level connections, it should be treated as **data
> linkage** for governance purposes unless national rules explicitly provide
> otherwise."

Source: TEHDAS2 M5.4, Section 4.2.1

**Audit implication**: Any document describing person-level joins across data
permits without explicit Art. 68(1)(b) HDAB approval is a critical violation
(EHDS-SEC-LINK-002).

## Example — True Data Linkage (needs HDAB approval)

A research team applies to an HDAB requesting to link:
- Electronic health records (category a)
- National mortality register (category l)
The HDAB performs the record-level linkage and provides only the final combined
dataset. The user never sees unlinked raw records.

## Example — True Enrichment (does NOT need separate linkage approval)

A researcher with an approved dataset appends area-level deprivation scores
from publicly available data — no person-level matching occurs.

## EHDS Workflow for Data Linkage

```
APPLICATION (Art.68)
  └─ User explicitly requests data linkage (Art.68(1)(b))
       │
       ▼
HDAB ASSESSMENT
  └─ Legal/ethical/technical review
  └─ Data minimisation check (Art.66): "adequate, relevant, limited"
       │
       ▼
DATA PERMIT ISSUED
  └─ Specifies datasets, operations, restrictions
       │
       ▼
DATA LINKAGE (pre-access, HDAB-managed)
  └─ Person-level matching across datasets
  └─ Only linked dataset provided to user
       │
       ▼
SPE ACCESS (post-access, user-driven)
  └─ Analysis, enrichment, results export
```

## KB Rules for Data Linkage

```
RULE_06: [Data Linkage] → MUST_REQUEST → [Explicit HDAB Approval Art.68(1)(b)]
         AND [Pre-Access Management]

RULE_07: [External Enrichment w/ Record-Level Match] → TREAT_AS → [Data Linkage]
         → REQUIRES → [Separate Approval]
```

## Audit Rules (ehds_common.py)

```
EHDS-SEC-LINK-001 (critical):
  Missing data linkage governance: no HDAB pre-access approval reference (Art.68)
  Keywords: ["data linkage", "record linkage", "dataset combination", "linkage approval"]

EHDS-SEC-LINK-002 (high):
  Record-level matching without explicit Art.68(1)(b) data permit request
  Keywords: ["article 68", "art.68", "data permit", "pre-access", "hdab managed linkage"]
```

## Forthcoming

TEHDAS2 is developing a dedicated "Guideline for Health Data Access Bodies on
Linkage of Health Datasets" (consultation wave 3, May 2026). Will supersede
the enrichment guideline's linkage sections.

## Source PDF

`data/source_pdfs/draft-guideline-for-data-enrichment.pdf` — TEHDAS2 M5.4,
pages 12-13, 19-20, 44 (glossary).
