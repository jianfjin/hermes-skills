---
name: ehds-symbolic-wiki-construction
description: Method for transforming evolving regulatory frameworks into a computable knowledge base using a blend of symbolic logic (Graph) and semantic retrieval (Vector) to ensure high precision and traceability.
---

# Neuro-Symbolic Compliance Knowledge Graph (S-Wiki)

## Overview
This skill defines a method for building a "Cognitive Mesh" over regulatory frameworks (e.g., EHDS). By blending symbolic logic (Graphs/Wiki-links) with semantic retrieval, it eliminates the "blurriness" of standard RAG and enables "regulatory arbitrage" by mapping how rules evolve across versions (R1 $\rightarrow$ R2 $\rightarrow$ R3).

## Trigger Conditions
- When analyzing regulatory documents that evolve across multiple iterations.
- When high precision and deterministic traceability are required (e.g., legal auditing).
- When the goal is to identify specific "traps" or "loopholes" caused by changes in official wording.

## Implementation Steps

### 1. Atomic Decomposition
Break the regulatory body into atomic, non-overlapping nodes:
- **Article Nodes**: Raw legal text fragments.
- **Constraint Nodes**: Specific "shall" or "must" requirements extracted from articles.
- **Risk Nodes**: Financial/legal penalties tied to specific constraints.
- **Remediation Nodes**: Practical "Correct Paths" to resolve risks.

### 2. Temporal Mapping (Evolutionary Tracking)
Tag nodes with version identifiers (e.g., `#S_R1`, `#S_R2`, `#S_R3`).
- Establish `superseded_by` links to track the lifecycle of a rule.
- Identify "Sovereign Risks" by analyzing where requirements tightened between versions.

### 3. Structural Mesh (MOCs)
Create Maps of Content (MOCs) as high-level entry points.
- A `SecondaryUse_MOC` should serve as the root for all related constraints and risks.
- Use bi-directional linking to allow the Agent to traverse the graph without losing context.

### 4. Hybrid Retrieval Pipeline (O(log N))
- **Router Stage**: Classify the query to a specific MOC root.
- **Traversal Stage**: Move from MOC $\rightarrow$ Branch $\rightarrow$ Atomic Leaf.
- **Synthesis Stage**: Use the logical symbolic path to constrain the LLM, preventing "semantic hallucinations."

## Concrete Implementation: Three-Layer Knowledge Stack

For production regulatory auditing (e.g., EHDS), map the abstract model to a concrete
three-layer directory structure with YAML frontmatter and MCP tool exposure.

### Layer 1: Index (Authoritative Legal Text)

**Directory:** `ehds_index/`

One file per Article. Never contains interpretation — only regulation text plus
machine-parseable anchors.

**File naming:** `EHDS-{YYYY}-{NNN}_Art-{AAA}.md`

**Frontmatter schema:**
```yaml
---
regulation: "Reg. (EU) 2025/327"
article: 54
title: "Permitted purposes for secondary use — scientific research"
chapter: "V"
stable_id: "EHDS-2025-327-A54"   # Immutable forever
category: "secondary_use"
date_enacted: "2025-03-11"
---
```

**Body structure:**
- `# Art. N — Title`
- `## Para N` for each paragraph
- `## Audit Anchors` section with `[[A54-P2]] :: description` syntax

See `references/frontmatter-schemas.md` and `templates/index-article.md` for exact
starter files.

See `templates/ehds-embedding.py` for the semantic search engine template.
See `templates/batch-import.py` for the bulk Article import template.
See `scripts/verify-semantic-search.py` for a quick pipeline health check.

### Layer 2: Wiki (Semantic Associations)

**Directory:** `ehds_wiki/`

Human-readable context plus machine-parseable metadata. Preserves `[[WikiLink]]`
semantic graph.

**Frontmatter schema:**
```yaml
---
wiki_id: "WIKI-SEC-001"
title: "Secondary Use of Health Data"
regulation: "Reg. (EU) 2025/327"
article: 54
category: "secondary_use"
keywords: ["scientific research", "HDAB approval"]
index_refs: ["EHDS-2025-327-A54", "EHDS-2025-327-A55"]
anchors: ["A54-P1", "A54-P2"]
created: "2026-05-08"
updated: "2026-05-11"
author: "CTO-FengGe"
---
```

### Layer 3: KB (Machine-Actionable Rules)

**Directory:** `ehds_kb/`

Prompt templates, heuristic rules, regex detectors, JSON-LD output schemas.

### Citation Resolution Engine

Build a resolver that accepts multiple citation formats and maps them to the
single `stable_id`:

| Format | Example | Resolved To |
|--------|---------|-------------|
| Stable ID | `EHDS-2025-327-A54` | Full Article 54 |
| Stable ID + Anchor | `EHDS-2025-327-A54-P2` | Paragraph 2 of Art. 54 |
| Article ref | `Art. 54` | Article 54 |
| Article + Paragraph | `Art. 54(2)` | Paragraph 2 of Art. 54 |
| Full legal cite | `Reg. (EU) 2025/327, Art. 54(2)` | Paragraph 2 of Art. 54 |

### MCP Tool Exposure

Expose the stack via Model Context Protocol so any agent (Claude, Cursor, Agno)
can audit documents without replicating the knowledge base.

**Key tools:**
- `resolve_citation(citation)` → authoritative text + anchor snippet
- `audit_document(path, purpose_tags)` → JSON-LD violation array
- `search_kb(query)` — full-text AND search across all layers
- `list_documents(layer="index")` — browse with layer filter

**Audit output schema (JSON-LD):**
```json
{
  "@context": "https://schema.org",
  "@type": "AuditReport",
  "audit_status": "completed",
  "document": "drive_ehds_docs_r2/draft-guideline.pdf",
  "severity_summary": {"critical": 1, "high": 2, "medium": 0, "low": 0},
  "violations": [{
    "rule_id": "EHDS-SEC-AUTH-001",
    "ehds_citation": "EHDS Reg. (EU) 2025/327, Art. 54(2)",
    "violation_type": "missing",
    "severity": "critical",
    "description": "...",
    "location": {
      "page": null,
      "bbox": null,
      "line_estimate": 0,
      "extraction_method": "pymupdf"
    },
    "remediation": "Add explicit HDAB authorisation requirement..."
  }]
}
```

### Path Resolution Guard

When building MCP tools that resolve user-provided paths against KB_ROOTS:
1. **First try:** Resolve relative to `HERMES_HOME` (e.g. `docs/ehds_wiki/Foo.md`).
2. **Second try:** Resolve relative to each KB root directly (e.g. `EHDS-2025-327_Art-054.md`).
3. **Verify:** Ensure resolved path is still inside at least one KB root (traversal guard).
4. **Reject:** Symlinks pointing outside KB roots.

Skipping step 1 causes paths like `docs/ehds_wiki/Foo.md` to fail when the tool
naively prepends a KB root instead of `HERMES_HOME`.

### Deployment & Validation Pipeline

After building the three-layer stack, run a structured deployment validation
before claiming production readiness.

#### Step 1: End-to-End Test Script

Write `test_e2e.py` that imports the MCP server module and validates:
- **Index layer:** All expected stable IDs load, anchors parse, article numbers match
- **Citation resolution:** Every supported format (stable_id, stable_id+anchor, Art. N, Art. N(para), full legal cite) resolves correctly
- **Wiki layer:** Every `.md` file has valid YAML frontmatter with `wiki_id`, `index_refs`, `article`
- **KB layer:** All rule files exist
- **Path security:** Directory traversal attacks are blocked
- **Audit engine:** A known-non-compliant document triggers expected violations; a compliant document triggers ≤1 false positive
- **Architecture doc:** The `THREE_LAYER_ARCHITECTURE.md` exists and references all three layers

Run: `python3 test_e2e.py` — exit code 0 means all checks passed.

See `scripts/test_e2e.py` for a starter template.

See `templates/ehds-api-server.py` for a starter HTTP gateway template.

#### Step 2: HTTP API Gateway (Optional but Recommended)

Wrap the MCP tools in a lightweight HTTP server for browser-based dashboards
and non-MCP clients.

**Endpoints to expose:**
- `GET /` — HTML dashboard showing layer counts and document lists
- `GET /api/health` — service health + available layers
- `GET /api/stack` — JSON overview of all three layers
- `GET /api/index` — list Index documents with frontmatter metadata
- `GET /api/wiki` — list Wiki documents with frontmatter metadata
- `GET /api/kb` — list KB documents
- `GET /api/resolve?citation=Art.54(2)` — citation resolver
- `GET /api/audit?path=docs/ehds_kb/...` — compliance audit
- `GET /api/search?q=...` — full-text search across layers

**Implementation notes:**
- Use Python's built-in `http.server.HTTPServer` — no extra dependencies.
- Import the same `_load_index_entries()`, `_resolve_citation()`, `_parse_frontmatter()`, `_search_in_file()` helpers from the MCP server module to avoid logic drift.
- For the audit endpoint, inline the rule engine (you cannot call `@mcp.tool()`-decorated functions directly without the FastMCP framework).
- Serve on `0.0.0.0:8080` (or any free port).

See `templates/ehds-api-server.py` for a starter template.

#### Step 3: Browser-Based Acceptance Check

After starting the HTTP gateway, use the agent's browser tool (not just `curl`)
to verify the dashboard renders correctly:
1. Navigate to `http://localhost:8080/`
2. Execute JavaScript to read DOM values:
   - `#index-count`, `#wiki-count`, `#kb-count` should match expected file counts
   - `.layer-card` count should be 3
3. Navigate to `/api/resolve?citation=Art.54(2)` and verify JSON returns `found: true`
4. Navigate to `/api/audit?path=...` and verify JSON contains `severity_summary`
5. Navigate to `/api/search?q=HDAB+authorisation` and verify matches span multiple layers

**Why browser, not just curl?** The browser validates that the HTML dashboard
actually loads its data via JavaScript `fetch()` calls, catching CORS or async
loading bugs that curl would miss.

## Phase 3: LLM Reasoning Layer (Neuro-Symbolic Audit Engine)

After the three-layer stack is operational, replace pure keyword-matching with
a **neuro-symbolic reasoning pipeline**:

```
Phase 1: Keyword Pre-Filter        Phase 2: LLM Reasoning              Phase 3: Merge
┌──────────────────┐  ┌───────────────────────────────────┐  ┌──────────────────┐
│ 6 built-in rules │  │ TF-IDF → top-5 Index articles     │  │ LLM findings     │
│ + KB .md rules   │─▶│ WikiLinks → Wiki context         │─▶│ (priority)       │
│ (fast, always)   │  │ KB rules → Structured Prompt     │  │ + keyword        │
│                   │  │ DeepSeek LLM → Cited violations  │  │ (gap-fill)       │
└──────────────────┘  └───────────────────────────────────┘  └──────────────────┘
```

### Implementation

Extract the audit engine into a **shared module** (`ehds_audit_engine.py`):
- `audit_document_shared()` — keyword-only audit (always runs, no API key needed)
- `audit_document_llm()` — keyword pre-filter + LLM cross-layer reasoning
- `_build_llm_prompt()` — constructs structured prompt from Index/Wiki/KB layers
- `_call_llm()` — OpenAI-compatible API call with graceful fallback

Both `ehds_mcp_server.py` and `ehds_api_server.py` import from this single module
(eliminates code duplication — was previously copy-pasted).

### LLM Prompt Structure

The prompt feeds the LLM all three layers plus keyword pre-filter results:
1. INDEX LAYER — top-5 semantically relevant articles with full text
2. WIKI LAYER — top-5 Wiki entries with contextual explanations
3. KB RULES — parsed machine-actionable rules from ehds_kb/*.md
4. KEYWORD PRE-FILTER — violations already detected
5. DOCUMENT TO AUDIT — the target text
6. TASK — "Find violations the keyword filter missed. Cite exact articles. Output JSON."

LLM output is parsed as JSON with `llm_violations` and `llm_recommendation` fields,
then merged with keyword results (LLM findings take precedence).

### Fallback Strategy

| Condition | Behavior |
|-----------|----------|
| `DEEPSEEK_API_KEY` set | Full neuro-symbolic pipeline |
| No API key / `openai` not installed | Keyword-only, `audit_method: "keyword-only"` |
| LLM call timeout/error | Keyword results returned, `llm_note` explains omission |

### Integration into Existing RAG (edm_home pattern)

Create an `EHDSKGRetriever` class with a `retrieve(query, depth)` method:
- `depth=0` — Index exact match (citation lookup)
- `depth=1` — Index + TF-IDF semantic search across Wiki
- `depth=2` — Full stack including KB rules + LLM audit reasoning

Add `depth: int = 1` to the existing ChatRequest model — one parameter, three
levels of KG depth. The KG becomes a pluggable retrieval source alongside
existing vector/hybrid strategies.

### Semantic Search Engine

Goal: enable queries like *"HDAB approval requirements"* to return Art. 59
(Index) and HDAB_Approval (Wiki) even when the exact keywords differ.

#### Option A: Neural Embeddings (sentence-transformers)

Use `all-MiniLM-L6-v2` (384-dim) for high-quality semantic similarity.
- **Pro**: understands paraphrase and conceptual similarity
- **Con**: model load takes 30–60s on CPU; `encode()` can hang on VMs with <2GB RAM
- **When to use**: development workstations, GPU-enabled servers, or after model cache is warm

#### Option B: TF-IDF + Cosine Fallback (Resource-Constrained VMs)

On VMs with ≤2 CPU cores and ≤2GB RAM, sentence-transformers often deadlocks
or OOMs during first `encode()`.  Use `sklearn.feature_extraction.text.TfidfVectorizer`
as a lightweight fallback:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer(
    stop_words="english", ngram_range=(1, 2),
    max_features=5000, min_df=1, max_df=1.0
)
```

- **Chunking**: split each Index Article by `## Para N`; split Wiki/KB by paragraph
- **Matrix**: sparse TF-IDF matrix, one row per chunk
- **Search**: `chunk_matrix * query_vec.T` → cosine similarity scores
- **Latency**: <0.05s for 100+ chunks on a 2-core VM
- **Quality**: surprisingly good for legal text because terminology is precise and vocabulary is small

**Decision rule**: try neural first; if `encode()` does not return within 10s on
the target VM, fall back to TF-IDF immediately.  Do not spend more than one
retry cycle debugging a hung model load on a constrained VM.

See `templates/ehds-embedding.py` for a complete engine template with both
backends and automatic fallback.

#### Singleton Caching Pattern

Whether using neural or TF-IDF, the engine **must** be a global singleton:

```python
_engine_instance: Optional[EmbeddingEngine] = None

def get_engine() -> EmbeddingEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EmbeddingEngine()
    return _engine_instance
```

Per-request instantiation causes the API gateway to hang for 30–60s on the
first semantic_search call.  Pre-loading at startup is also risky because the
model load blocks the main thread and can trigger HTTP client timeouts before
the server finishes booting.  Lazy singleton is the safest default.

**Process restart after index rebuild**: when `batch_import.py --build` or
`ehds_embedding.py --build` runs, it writes new `.pkl` / `.db` files.  The
running API server still holds the old in-memory matrix.  Always kill and
restart the API process after rebuilding the index, or the next semantic_search
will throw "index N is out of bounds for axis 0 with size M".

### PDF Structured Extraction for Audit

For legal-grade audit reports, text-only extraction is insufficient — you need
**page, bounding-box, and line coordinates** so violations can be located in
the original PDF.

Use PyMuPDF (`fitz`) to extract text blocks with coordinates:

```python
import fitz  # PyMuPDF

def _read_pdf_file_structured(path: Path) -> List[Dict[str, Any]]:
    doc = fitz.open(str(path))
    blocks: List[Dict[str, Any]] = []
    line_estimate = 1
    for page in doc:
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text, *_ = block
            blocks.append({
                "page": page.number + 1,
                "bbox": [x0, y0, x1, y1],
                "text": text.strip(),
                "line_estimate": line_estimate,
            })
            line_estimate += text.count("\n") + 1
    return blocks
```

In the audit rule engine, pass a `locator_keyword` (e.g. `"scientific"` for an
ethics-committee violation) and match it against block text.  The resulting
`location` object in the JSON-LD violation now contains exact `page` and `bbox`.

### Batch Import Tooling

When scaling from a handful of Articles to 30+, manual file creation is
unsustainable.  Build a `batch_import.py` script with two modes:

1. **Source split mode**: input is one large markdown file with headers like
   `## Article 33` or `## Art. 33`.  The script splits on these headers,
   auto-generates Frontmatter + stable_id + paragraph anchors, and writes one
   `.md` per Article into `ehds_index/`.

2. **Skeleton generation mode**: `python3 batch_import.py --generate-skeleton`
   creates placeholder Articles for a known range (e.g. Arts. 33–67) using
   public summaries or a seed corpus.  This lets you stand up the full Index
   structure in minutes, then backfill with real regulation text later.

Both modes must preserve existing high-quality files (check `stable_id` match)
and only overwrite when `--overwrite` is passed.

See `templates/batch-import.py` for the full script template.

### Expanded API Endpoints (Phase 2)

Add to the HTTP gateway:
- `GET /api/retrieve?q=...&depth=0|1|2&max_results=5` — **Primary retrieval endpoint.**
  Replaces in-process file reading with a single HTTP call. Depth levels:
  | depth | Layers | What it does |
  |-------|--------|-------------|
  | 0 | Index only | Citation lookup + token-based keyword match against legal articles |
  | 1 | Index + Wiki | depth=0 + TF-IDF semantic search across all layers (604 chunks, 5000 vocab) |
  | 2 | Full stack | depth=1 + compliance audit rules (EHDS-SEC-*) with severity scoring |
  Returns JSON: `{query, depth, result_count, results: [{layer, document, section, similarity, text:800, source_path, ...}]}`
- `GET /api/semantic_search?q=...&top_k=N&layer=...` — TF-IDF or neural semantic search
- Enhanced `/api/audit` — includes `location.page`, `location.bbox` for PDFs

**Lazy engine loading**: Import `ehds_embedding.get_engine()` inside the handler,
not at module level. The TF-IDF singleton loads a 16MB SQLite + 453KB pickle —
doing this at import time blocks the server thread and causes client timeouts
before the first health check returns.

**HTTP client decoupling**: Downstream consumers (e.g., edm_home) call `/api/retrieve`
via `urllib.request` instead of reading KG files directly. Configure with
`EHDS_KG_API_URL` env var. This lets the KG run on a different host, VM, or behind
a Cloudflare tunnel without filesystem coupling.

Dashboard HTML should list `/api/retrieve` alongside the other endpoints
so operators know the capability exists.

See `references/api-retrieve-design.md` for the full API contract,
depth-level semantics, request/response schema, and client/server
implementation patterns.

## Pitfalls & Lessons Learned

### Architecture Integrity
- **KB Layer Must Drive the Rule Engine**: The KB layer (`ehds_kb/`) defines machine-actionable rules. The audit engine in `audit_document()` must read and execute those rules — not maintain a separate hardcoded set. If KB has `RULE_01` through `RULE_05` and the engine has 6 different rules with different IDs, the KB is dead code and every rule change requires editing Python in two places (mcp_server AND api_server). **Single source of truth: KB files define rules; engine loads and executes them.**
- **No Code Duplication Between Server and API**: The audit rule engine was copy-pasted verbatim between `ehds_mcp_server.py` and `ehds_api_server.py`. Extract the rule engine into a shared module (`ehds_audit_engine.py`) that both import.
- **Frontmatter Parser Must Use a YAML Library**: The current line-by-line string-split parser breaks on nested structures, lists with commas in values, quoted strings, and multi-line values. Use `import yaml` and `yaml.safe_load(frontmatter_block)`. The hand-rolled parser is a time bomb.
- **Stable IDs Must Be Unique**: Run a uniqueness check across all Index files before claiming the layer is valid. The audit found `Art-066.md` and `Art-66.md` both claiming `EHDS-2025-327-A66`.

### Performance
- **Cache `_load_index_entries()`**: It re-reads 35+ markdown files on every citation resolution and audit call. Cache in memory with a TTL (e.g. 5 min, store `_index_cache_time`). Within a single MCP tool invocation it may be called multiple times.
- **TF-IDF Parameters Matter**: `min_df=1, max_df=1.0` means zero filtering. On a 37-document legal corpus, boilerplate phrases like "electronic health data" appear in every file and dominate top TF-IDF terms. Set `min_df=2` and `max_df=0.85` to surface discriminating legal terminology.
- **TF-IDF Storage Is Wasteful**: `toarray().tolist()[0]` converts sparse vectors to dense JSON arrays — ~50KB per chunk in SQLite. Store as sparse or rebuild from SQLite on load.

### Security
- **NEVER `pickle.load()` on a predictable path**: `~/.hermes/docs/ehds_tfidf.pkl` is an RCE vector if another process can write there. Store vocabulary + idf as JSON; rebuild the sparse matrix from SQLite on load. Add staleness check (`chunk_count` in cache vs actual DB rows) so stale caches auto-rebuild.
- **API server must not bind 0.0.0.0 with CORS wildcard and zero auth**: The HTTP gateway serves internal compliance documents and audit logic. At minimum, bind `127.0.0.1` or add API-key authentication.

### Data Integrity
- **Case-sensitivity consistency**: Always check against `lowered` text in keyword rules. NEVER mix `doc_text` and `lowered` in the same conditional — e.g. `"SCC" not in doc_text` vs `"adequacy" not in lowered` produced a silent false-negative where lowercase "scc" would never match.

### Security
- **`pickle.load()` on a Predictable Path Is RCE**: `ehds_embedding.py` unpickles from `~/.hermes/docs/ehds_tfidf.pkl`. Any process that can write to that path gets arbitrary code execution on server start. Either: (a) use a safer serialization format (joblib with `mmap_mode`, or numpy `.npy` for the matrix + JSON for the vectorizer config), or (b) validate a checksum before unpickling.
- **API Server Binds 0.0.0.0:8080 with CORS Wildcard and Zero Auth**: The HTTP gateway serves internal compliance documents and audit logic to the entire network. At minimum: bind to `127.0.0.1` by default, require the same `X-EDM-Service-Key` header that `rag_server.py` already validates, and restrict CORS origins.

### Bugs to Watch For
- **Case-Sensitivity Inconsistency in Audit Rules**: Cross-border rule checks `"SCC" not in doc_text` (original case) alongside `"adequacy" not in lowered` (lowercased). A document containing `"scc"` will never match. All keyword checks within a single rule must use the same case normalization.
- **`purpose_tags` Parameter Is Accepted But Unused**: The `audit_document` tool signature includes `purpose_tags` but zero audit rules reference it. Either wire it into rule gating or remove it from the signature.
- **Layer Detection via String Matching Is Fragile**: `_walk_kb()` uses `"ehds_index" in str(path)` to classify layers. A file named `my_ehds_index_notes.md` anywhere under HERMES_HOME would be misclassified. Compare against the resolved KB_ROOT path directly.
- **PDF `location` Coverage Is Incomplete**: Only 3 of 6 audit rules pass a `locator_keyword` to `_add_violation()`. The other 3 rules produce violations with `page: null, bbox: null` even for PDFs where PyMuPDF is available.
- **Cyclic Import Between `ehds_embedding` and `ehds_mcp_server`**: `ehds_embedding.py` imports `ehds_mcp_server` for `_parse_frontmatter()`, while `ehds_mcp_server.py` lazy-imports `ehds_embedding` for `semantic_search()`. Extract shared utilities (`_parse_frontmatter`, `_read_text_file`, `_resolve_kb_path`) into `ehds_common.py` that both import without cycles.

- **Chunk Dedup Kills Body Text in RAG Retrieval (2026-05-12)**: When the retriever
  deduplicates TF-IDF semantic search results by `source_path`, only the first chunk
  survives. For Wiki entries split by `\n\n`, the first chunk is typically the heading
  (`# Title`). All body content chunks from the same file are silently dropped because
  they share the same `source_path`. The LLM receives 50 chars of title and generates
  "the provided context does not contain definitional content."

  **Detection**: curl the deployed RAG API with a known-good query. If the answer says
  "only the heading" or "context does not contain" but the source file has substantive
  body text, dedup is the culprit.

  **Fix**: After semantic search identifies matching source files, **read the full file
  body** (strip YAML frontmatter, cap at 2000 chars) instead of relying on chunk-level
  snippets. The TF-IDF engine is used for *discovery* (which file matches), not for
  *content extraction* (what text to send to the LLM).

  Implementation:
  ```python
  for sr in semantic_results:
      sp = sr.get("source_path", "")
      full_path = kg_path / sp
      full_text = full_path.read_text(...)
      # strip frontmatter, take body[:2000]
  ```

  Do NOT trust chunk-level `text` from `semantic_search()` — it's a single paragraph
  fragment. Always read the source file for rich context after discovery.

- **Path Staleness After KG Migration**: Moving the KG from `~/.hermes/docs/` to a
  standalone `~/projects/ehds_kg/` breaks every downstream consumer that hardcodes the
  old path. The RAG backend (`ehds_kg.py` in edm_home), MCP server, and API gateway all
  need their path constants updated. After migration, curl the deployed API with a
  known-good query — if it returns empty, check whether the backend is still pointing at
  the old (now empty) location. The TF-IDF cache files are path-relative; rebuild after
  migration.

- **Index Substring Matching Produces False Positives**: `query_lower in body_lower`
  matches \"Art 5\" against \"Art 50\", \"Art 51\", ... \"Art 59\". Returns every article
  containing the substring, zero relevance ranking, arbitrary dict-iteration order.
  For citation lookup this is dangerous — wrong article citations undermine compliance
  audits. **Fix**: tokenize query on word boundaries (`re.findall(r\"[a-z0-9]+\", query)`),
  require ALL tokens to appear in article text. For article numbers, match exact stable_id
  before falling back to token intersection.

- **Templates Import Non-Existent `ehds_mcp_server`**: Every template in this skill (`ehds-api-server.py`, `ehds-embedding.py`, `test_e2e.py`, `verify-semantic-search.py`) has `import ehds_mcp_server as mcp` — a module that only exists inside the Hermes Agent MCP framework, not as a standalone file. The templates will fail with `ModuleNotFoundError` if run outside Hermes. **Fix**: either (a) keep the KG inside Hermes and use its MCP server, or (b) migrate to a standalone project by creating `ehds_common.py` with all shared utilities extracted (`_parse_frontmatter`, `_load_index_entries`, `_resolve_citation`, `_resolve_kb_path`, `_walk_kb`, `_search_in_file`, `audit_document`), replace all `HERMES_HOME` references with `PROJECT_ROOT`, and update all imports. See `references/standalone-migration.md` for the full procedure.

## Systematic PDF Ingestion (CRITICAL — learned 2026-05-12)

When the user provides source PDFs (e.g., TEHDAS2 consultation documents), do NOT treat
them as raw reference files. Extract ALL substantive topics into the Wiki layer.
A knowledge base with 12 PDFs sitting in `data/` and only 8 Wiki entries is a skeleton,
not a functional KG. The user WILL test with random queries and expects answers.

**Ingestion workflow:**

1. **Group PDFs by domain** (e.g., HDAB ops, data subjects, infrastructure) — 3-4 PDFs per group.
2. **Delegate to parallel subagents** via `delegate_task` — one subagent per group.
   Each subagent reads its PDFs with PyMuPDF (`fitz`), extracts key topics, and writes
   Wiki entries with full YAML frontmatter.
3. **Wiki entry requirements**: minimum 1500 chars of real extracted content. Include
   definitions, key points, EHDS article references, practical examples, pitfalls.
   Use `[[WikiLink]]` cross-references to existing entries.
4. **Update MOC**: after adding Wiki entries, update `EHDS_SecondaryUse_MOC.md` to
   add links to new entries in the appropriate section.
5. **Enrich Index articles**: if PDF content matches specific EHDS articles, add a
   "TEHDAS2 Implementation Guidance" section to the relevant `ehds_index/` file.
6. **Update KB rules**: add corresponding audit rules to `ehds_kb/secondary_use_rules.md`
   and the audit engine in `ehds_common.py`.
7. **Rebuild TF-IDF index**: `python3 src/ehds_embedding.py --build` — mandatory after
   any content change. The deployed RAG (knowledge.edmf.nl) needs this to pick up changes.
8. **Verify with random queries**: run 5-10 diverse semantic searches to confirm
   each topic returns the correct Wiki entry.

**Pitfall — skeleton syndrome**: If Index articles average <700 chars and Wiki has <10
entries despite 10+ source PDFs, the KG is a skeleton. Fix before the user notices.

## Verification
- Verify if the Agent can cite a specific version change to justify a risk rating.
- Check if the Agent identifies a "trap" that only emerged in the most recent version.
- **Post-ingestion test**: run 10 diverse semantic search queries — all should hit correct
  Wiki entries with similarity >0.2.
- **Pre-deployment audit**: See `references/audit-2026-05-11.md` for a comprehensive
  three-layer architecture audit (14 issues found, 8 critical/high).
- **Retrieval debugging**: See `references/retrieval-debugging.md` for a systematic
  4-level debugging ladder when deployed RAG returns empty/wrong answers — covers
  chunk dedup bugs, truncation misalignment, semantic gaps, and API layer issues.

- **Standalone migration**: See `references/standalone-migration.md` for extracting the KG from Paperclip/Hermes into an independent `~/projects/ehds_kg/` project that runs without Hermes MCP dependencies. Covers directory structure, `ehds_common.py` shared module creation, path refactoring, and f-string syntax fixes for Python 3.12+.

### Review Process Failure: Architecture Without Content (2026-05-12)

**What happened**: Inner Circle review debated three-layer architecture, TF-IDF parameters,
pickle security, path resolution — all technical concerns. Nobody asked: *"Take a random
query and see what the KG answers."* The KG had 37 Index skeletons (avg 680 chars), 8 Wiki
entries, and 12 unprocessed PDFs. When the user queried "explain data linkage in EHDS" via
knowledge.edmf.nl, the RAG returned empty generic response because zero entries contained
the concept. Architecture review passed with flying colors. Content review never happened.

**Root cause**: `test_e2e.py` validates structural correctness (frontmatter format, stable
IDs, anchor parsing, path security) but contains **zero content-level tests**. A KG passes
all structural checks while being completely unable to answer real queries.

**Mandatory Review Gate — insert BEFORE structural validation:**

1. **Source PDFs vs Wiki entries ratio**: If PDF count > Wiki entry count, the KG is a
   skeleton. HALT deployment. Ingest PDFs before proceeding.
2. **Index article depth check**: `wc -c ehds_index/*.md | sort -n`. If median < 500 chars,
   articles are placeholders. HALT.
3. **Random query test (minimum 5 questions)**: Pick concepts the KG should know. Run
   `semantic_search(query)` for each. If any returns similarity < 0.1 or wrong entry, HALT.
   If results come from only 1 of 3 layers, flag as thin.
4. **First reviewer's duty**: Ask "show me 3 random query results." If the reviewer cannot
   produce them within 30 seconds, the review has not started.

**Prevention**: Never claim production readiness until random queries return substantive,
multi-layer results. Architecture reviews are necessary but insufficient. Content is the
product — architecture is just the shelf.

## Bridging Semantic Gaps (Missing Concept Pattern)

When a RAG query like "explain data linkage in EHDS" returns empty or generic
results, the KG has a **semantic gap**: the concept exists in the regulation
but uses different terminology than the user's query.

### Detection

1. Search the Index for the user's exact term — if zero hits, it's a gap
2. Search source PDFs (TEHDAS2 guidelines, commission drafts) for the term
3. Identify which official terms ARE used ("secondary use", "cross-border exchange", "secure processing environment")

### Fix (Three-Layer Insertion)

1. **Wiki layer**: Create a new entry that defines the user-facing term, maps it to official terminology, and links to relevant Articles. The Wiki entry is the BRIDGE between user language and legal language.
2. **Index layer**: If the relevant Article is missing from the skeleton, create it with frontmatter and paragraph anchors. Even a skeleton with correct stable_id and anchor tags enables citation resolution.
3. **KB layer**: Add new rules that recognise the concept. Update `secondary_use_rules.md` with RULE_N entries.
4. **Audit engine**: Add corresponding `EHDS-SEC-*` rules in `ehds_common.py` `audit_document()`.
5. **Rebuild TF-IDF index**: `python3 src/ehds_embedding.py --build`
6. **Verify cross-layer retrieval**: Search for the term and confirm results span at least 2 of 3 layers.

### Data Linkage Example

See `references/data-linkage-domain.md` for the complete TEHDAS2-sourced
domain knowledge about data linkage vs. enrichment in EHDS, including the
critical governance distinction, legal basis (Art. 68(1)(b)), KB rules
(RULE_06, RULE_07), audit rules (EHDS-SEC-LINK-001/002), and the forthcoming
TEHDAS2 linkage guideline.

## API-First External Service Integration

External services query the KG via REST API — never by reading files directly.
Filesystem coupling prevents independent deployment and duplicates retrieval logic.

### Architecture

```
  consumer service          KG API server            KG filesystem
  (edm_home, etc.)          (ehds_api_server)        (~/projects/ehds_kg/)
        │                        │                         │
        │ GET /api/retrieve      │                         │
        │ ?q=...&depth=1         │                         │
        │ ──────────────────────→│ ehds_embedding          │
        │                        │ ehds_common             │
        │ ←──────────────────────│ ───────────────────────→│
        │ JSON {results:[...]}   │                         │
```

### /api/retrieve Endpoint

Single endpoint composing all depth levels:

```
GET /api/retrieve?q=<query>&depth=0|1|2&max_results=1-20
```

| Depth | Layers | Description |
|-------|--------|-------------|
| 0 | Index only | Token-based citation/keyword match |
| 1 | Index + Wiki + KB | TF-IDF semantic search (604 chunks) |
| 2 | + Audit engine | Compliance rule violations |

Response shape: `{query, depth, result_count, results: [{layer, document, section, similarity, text, source_path, ...}]}`

Full spec: `references/api-retrieve-spec.md` (request/response contract, error cases, depth semantics).

### HTTP Client (Consumer Side)

```python
class EHDSKGRetriever:
    def __init__(self, api_url="http://localhost:8080"):
        self._api_url = api_url  # overridable via EHDS_KG_API_URL env var

    def retrieve(self, query, depth=1, max_results=5):
        import urllib.request, urllib.parse, json
        params = urllib.parse.urlencode({
            "q": query, "depth": depth, "max_results": max_results
        })
        url = f"{self._api_url}/api/retrieve?{params}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
        context = "\n\n".join(
            f"[EHDS-{r['layer'].upper()}] {r.get('section','')}\n{r.get('text','')[:600]}"
            for r in data.get("results", [])
        )
        return context, data.get("results", [])
```

### Deployment

Consumer sets `EHDS_KG_API_URL`:
- Same VM: `http://localhost:8080` (sub-ms, zero external deps)
- Remote: `http://<host>:8080`
- Cloudflare tunnel: `https://wiki.edmf.nl` (CORS handled by API server)

### Anti-Pattern: Direct File Reads

NEVER have the consumer read `ehds_index/*.md` or `ehds_wiki/*.md` directly. This causes:
- Filesystem coupling (KG must be on same host)
- Duplicate retrieval logic (TF-IDF, citation resolution reimplemented)
- Stale cache issues (index rebuilds invisible to consumer)
- Path migration fragility (consumer breaks when KG moves)

The API server owns data + retrieval. Consumer is a thin client.
