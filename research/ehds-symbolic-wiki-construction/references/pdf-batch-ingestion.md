# EHDS PDF Batch Ingestion Workflow

Learned 2026-05-12. The user's frustration with skeleton-KB responses drove this process.

## When to Use

When the user provides 3+ source PDFs for the EHDS Knowledge Graph. Do NOT treat them
as raw reference files — extract ALL substantive topics into Wiki entries.

## Workflow

### 1. Audit Current State
```bash
cd ~/projects/ehds_kg
ls ehds_wiki/           # how many entries?
wc -c ehds_index/*.md   # how rich are articles?
ls data/source_pdfs/    # how many PDFs waiting?
```

Red flags: Wiki <10 entries despite 10+ PDFs, Index articles averaging <700 chars.

### 2. Group PDFs by Domain
Split PDFs into 3-4 groups by topic (e.g., HDAB operations, data subjects, infrastructure).
3-4 PDFs per group is the sweet spot — subagents can process this in 5-8 minutes.

### 3. Parallel Subagent Delegation
Use `delegate_task` with one task per group. Each subagent:
- Reads PDFs with `python3 -c "import fitz; doc = fitz.open('...'); print(doc[i].get_text())"`
- Extracts key topics, definitions, processes, examples
- Writes Wiki entries to `~/projects/ehds_kg/ehds_wiki/` with full YAML frontmatter
- Minimum 1500 chars of real content per entry
- Uses `[[WikiLink]]` cross-references to existing entries

### 4. Frontmatter Template
```yaml
---
wiki_id: "WIKI-XXX-001"
title: "Title Here"
regulation: "Reg. (EU) 2025/327"
article: "relevant articles"
category: "secondary_use"
keywords: ["kw1", "kw2"]
index_refs: ["EHDS-2025-327-A54"]
anchors: []
created: "2026-05-12"
updated: "2026-05-12"
author: "CTO-FengGe"
confidence: "high"
sources: ["data/source_pdfs/filename.pdf"]
---
```

### 5. Post-Ingestion Checklist
- [ ] Update `EHDS_SecondaryUse_MOC.md` — add links to new entries
- [ ] Enrich Index articles if PDF content matches specific EHDS articles
- [ ] Add KB audit rules for new compliance topics
- [ ] Update audit engine in `src/ehds_common.py`
- [ ] Rebuild TF-IDF: `python3 src/ehds_embedding.py --build`
- [ ] Run 10 diverse semantic search queries to verify
- [ ] Commit and push to git

### 6. Verification Queries
Run at least 5 diverse queries covering ALL new Wiki entries:
```python
from ehds_embedding import EHDSEmbeddingEngine
engine = EHDSEmbeddingEngine()
for q in ["data linkage", "opt-out mechanism", "SPE requirements", ...]:
    results = engine.semantic_search(q, top_k=1)
    print(f"{q} => {results[0]['source_path']}")
```

## Pitfalls

- **Skeleton syndrome**: Index articles from `batch_import.py --generate-skeleton` have
  placeholder content. PDF ingestion is what gives them real meat.
- **Missing Art.68**: The data access application article was missing from the Index.
  When a PDF references an article not in the Index, create it — don't just skip.
- **Single-source answers**: If only one Wiki entry matches across 10 queries,
  the KG is too sparse. Each major concept in each PDF needs its own entry.
- **Stale RAG**: After rebuilding the TF-IDF index, the deployed RAG (knowledge.edmf.nl)
  still has the old index in memory. Restart or redeploy.
