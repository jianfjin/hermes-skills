---
name: neuro-symbolic-compliance-kb
description: Constructing a "Cognitive Mesh" (Karpathy-style LLM Wiki) for regulatory compliance (e.g., EHDS) utilizing atomic nodes, version tracking, and symbolic linking to prevent hallucinations and enable gap analysis.
---

# Neuro-Symbolic Knowledge Graph Construction for Regulatory Compliance

## Overview
This skill outlines a high-fidelity approach to building a "Cognitive Mesh" for complex regulatory environments. It moves away from simple RAG (vector search) toward a symbolic-first, atomic-linked structure that allows for logical reasoning and regulatory "gap analysis."

## Trigger Conditions
- When building a knowledge base for legal/regulatory compliance where precision is non-negotiable.
- When the source material consists of multiple iterations/versions of guidelines (e.g., Consultation Round 1 $\rightarrow$ 2 $\rightarrow$ 3).
- When the agent needs to perform "Gap Analysis" or identify "Regulatory Arbitrage" opportunities.

## The Workflow

### 1. Atomic Decomposition (The Wiki Method)
Instead of simple chunks, break documentation into **Atomic Nodes**:
- **Nodes**: Each node is a single, verifiable claim or constraint (e.g., `[[Article_X]]`, `[[Constraint_Y]]`).
- **Format**: Markdown files with unique IDs.
- **Properties**: Each node must carry metadata:
    - `Version`: (e.g., `#ROUND_1`, `#ROUND_3`).
    - `Strictness`: (e.g., `MANDATORY`, `RECOMMENDED`).
    - `Risk_Level`: (e.g., `CRITICAL_FINANCIAL_RISK`).

### 2. Construction of the Cognitive Mesh
Establish explicit symbolic links to create a traversable graph:
- **Vertical Links**: `[[Rule]]` $\rightarrow$ `[[Requirement]]` $\rightarrow$ `[[Technical_Implementation]]`.
- **Temporal Links**: `[[Node_R1]]` $\xrightarrow{superseded\_by}$ `[[Node_R2]]` $\xrightarrow{finalized\_as}$ `[[Node_R3]]`.
- **MOCs (Maps of Content)**: Create entry-point nodes (e.g., `[[Secondary_Use_MOC]]`) that aggregate related atomic nodes for high-level context.

### 3. Execution Pipeline (The G-RAG Pattern)
1. **Route to MOC**: Identify which thematic domain the query belongs to.
2. **Graph Traversal**: Navigate from the MOC to the relevant atomic nodes.
3. **Version Delta Analysis**: Compare the current request against the `superseded_by` chain to identify "outdated logic" errors.
4. **Synthesis**: Use the LLM to generate the final report based on the traversed symbolic path.

## Pitfalls & Lessons Learned
- **The "Triviality Trap"**: Avoid over-engineering the UI. Keep the "Atomic Wiki" as the backend "Truth Machine" and the output as a "Pragmatic Tool" (Lean UI).
- **Vector Decay**: Pure vector search often misses "Hard Constraints" (e.g., "Must not do X"). Symbolic links ensure these constraints are never bypassed.
- **Version Drift**: Always tag documents by consultation round to avoid mixing obsolete guidelines with current ones.

## Phase 2: Semantic Search & Audit Precision Layer
Once the three-layer stack (Index / Wiki / KB) is stable, add machine-readable retrieval and legal-grade audit capabilities.

### 2.1 Lightweight Semantic Search
**Trigger**: The default neural embedding model (`sentence-transformers/all-MiniLM-L6-v2`) may hang indefinitely on `encode()` in RAM-constrained VMs (≤2 GB RAM, ≤2 vCPU).  
**Fallback**: Swap the neural encoder for a corpus-trained TF-IDF + cosine-similarity pipeline (`sklearn.feature_extraction.text.TfidfVectorizer`).  For legal text this performs nearly as well on keyword-semantic overlap and completes queries in <50 ms.
- Train on all Index paragraphs + Wiki body text.
- Cache the fitted vectorizer and sparse matrix to a pickle file; load at startup.
- Expose via MCP tool `semantic_search(query, top_k, layer)` and REST endpoint `/api/semantic_search`.

### 2.2 Structured PDF Extraction for Audit Location
Use **PyMuPDF** (`fitz`) to extract not only plain text but also per-block coordinates:
- `page`: 0-based page number
- `bbox`: `[x0, y0, x1, y1]` rectangle in PDF points
- `line_estimate`: approximate line number derived from block order
Store these blocks alongside the audit.  When a violation rule fires (e.g., missing ethics committee reference in a research clause), pass a `locator_keyword` to the block matcher so the JSON-LD violation object contains an exact `location.page` + `location.bbox`.

### 2.3 API Gateway Integration Pattern
- Use a **global singleton** (`get_engine()`) for the embedding/TF-IDF engine so the model is loaded once and reused across requests.  **Do not** pre-load at startup on single-threaded servers — it blocks the main thread and causes health-check timeouts before the server finishes booting.  Lazy singleton is safer.
- If using Python's built-in `BaseHTTPServer`, remember it is **single-threaded**; heavy initialization must happen **before** `serve_forever()` or the first request will block the server indefinitely.
- Pre-load with `HF_HUB_OFFLINE=1` when HuggingFace models are involved to prevent network stalls on isolated VMs.
- **Restart the API process after every index rebuild**. The embedding engine caches the sparse matrix in memory; rebuilding the index changes the matrix shape and the old process will throw index-out-of-bounds on the next search.

## Verification
- Can the agent explicitly cite the version of the guideline it is using?
- Can the agent identify a specific contradiction between an earlier version and a later version of the regulation?
- Does a semantic query for "HDAB approval requirements" return the correct Wiki article within 100 ms?
- Does a PDF audit report include exact `page` and `bbox` for every locatable violation?

## Phase 2 Enhancements (2026-05-12 — Inner Circle Debate)

### Enhanced Frontmatter Schema
See `references/enhanced-frontmatter-schema.md` for the post-debate schema
incorporating Temporal KG (valid_from/valid_to) from MemPalace and Confidence
Tagging (EXTRACTED/INFERRED/AMBIGUOUS) from Graphify.

### TF-IDF Semantic Engine
See `scripts/paperclip_tfidf.py` for the standalone Python module (Linus-spec
~150 lines, singleton, no external DB). Import via:
```python
from paperclip_tfidf import get_engine
engine = get_engine(kb_roots=["ehds_index/", "ehds_wiki/"])
results = engine.search("HDAB approval requirements", top_k=5)
```
Caches to `~/.hermes/cache/paperclip_tfidf.pkl`. Auto-rebuilds when KB files
change (staleness check via mtime).

## Project Location (2026-05-12)

The EHDS Knowledge Graph has been migrated from Paperclip to a standalone project:
`~/projects/ehds_kg` (git remote: `github.com/jianfjin/ehds_kg`).

Key paths:
- `ehds_index/` — 37 Articles (Layer 1)
- `ehds_wiki/` — 20 Wiki entries (Layer 2)
- `ehds_kb/` — 2 rule files (Layer 3)
- `src/ehds_common.py` — Shared utilities, citation resolver, audit engine
- `src/ehds_embedding.py` — TF-IDF semantic search (604 chunks, 5000 vocab)
- `src/ehds_api_server.py` — HTTP API gateway (port 8080)
- `data/source_pdfs/` — 12 TEHDAS2 consultation PDFs
- `cache/` — TF-IDF pickle + embeddings DB

All paths use `PROJECT_ROOT` (resolved from `ehds_common.py`), not `HERMES_HOME`.
The deployed RAG service is at `knowledge.edmf.nl` — needs index rebuild after content changes.

For **standalone migration** (extracting the KG from Paperclip/Hermes MCP into
an independent `~/projects/ehds_kg/` project), see `ehds-symbolic-wiki-construction`
→ `references/standalone-migration.md`.

For **data linkage** domain knowledge (linkage vs. enrichment, TEHDAS2 M5.4,
Art. 68(1)(b) legal basis, audit rules EHDS-SEC-LINK-001/002), see
`ehds-symbolic-wiki-construction` → `references/data-linkage-domain.md`.
