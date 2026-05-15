# Retrieval Debugging: Why Is My RAG Returning Empty/Generic Answers?

Systematic debugging for KG+RAG systems when a query returns empty, truncated,
or irrelevant results despite the knowledge base having the content.

## Debugging Ladder (bottom-up)

### Level 1: Is the content actually in the KG?

```bash
# Direct file search
grep -ril "target term" ehds_index/ ehds_wiki/ ehds_kb/

# TF-IDF chunk search
python3 -c "
from ehds_embedding import EHDSEmbeddingEngine
e = EHDSEmbeddingEngine()
for r in e.semantic_search('query', top_k=10):
    print(f'{r[\"similarity\"]:.3f} | {r[\"layer\"]:6s} | {r[\"source_path\"]}')
"
```

If semantic_search returns results but the deployed RAG doesn't → Level 2.
If semantic_search returns nothing → Level 3 (content gap).

### Level 2: Is the retrieval pipeline dropping results?

Check each layer in the retrieval chain:

1. **Dedup logic**: Does `_add_result` kill chunks from the same file?
   - Symptom: semantic_search returns 5 results from Data_Linkage.md, but only 1 makes it to the LLM
   - Fix: use chunk-level dedup keys, not source_path

2. **Chunk vs full-file**: Does the retriever rely on chunk-level snippets?
   - Symptom: LLM sees only heading text ("# Data Linkage"), not body
   - Root cause: TF-IDF chunks are per-paragraph. The highest-ranked chunk is often the
     heading/intro. If dedup kills subsequent chunks, body text never reaches the LLM.
   - Fix options:
     A) Read full file body after TF-IDF discovers the matching file
     B) Merge top-N chunks from same source_path in document order
     C) Pre-compute file-level summaries at index time

3. **Truncation misalignment**: Does the retriever read 2000 chars but the context
   builder truncates to 300?
   - Symptom: content exists in source dicts but context_text is too short
   - Fix: align read size with context builder truncation

4. **Layer dedup collision**: Do different layers share a `seen_ids` set?
   - Symptom: Index result with same parent_id as Wiki result → one silently dropped
   - Fix: namespace parent_ids by layer prefix (`idx-{sid}`, `wiki-{path}`, `audit-{rule_id}`)

### Level 3: Is there a semantic gap?

The concept exists in regulation but uses different terminology than the query.
See "Bridging Semantic Gaps" in the main SKILL.md.

1. Search source PDFs for the user's term
2. Identify official terminology used in regulation
3. Create Wiki entry bridging user language → legal language
4. Add Index articles if missing
5. Update KB rules and audit engine
6. Rebuild TF-IDF index

### Level 4: Is the API layer broken?

For service-decoupled architectures (edm_home → ehds_kg API):

1. Does the API endpoint exist? `curl localhost:8080/api/retrieve?q=...`
2. Is the API server running the latest code? (file modification ≠ server restart)
3. Is the Cloudflare tunnel forwarding all paths? (test `/api/health`, `/api/stack`, `/api/retrieve`)
4. Does the HTTP client have the correct URL? (localhost vs tunnel vs remote)
5. Are CORS headers present for browser clients?

## Concrete Debugging Session (2026-05-12: "data linkage" query)

### Symptom
User queried knowledge.edmf.nl: "explain data linkage in EHDS"
Response: "Cannot explain — only saw a heading."

### Debugging ladder

**Level 1 — Content check:**
- `grep -ril "linkage" ehds_wiki/` → empty (content gap, already fixed by adding Data_Linkage.md)
- After adding Data_Linkage.md + rebuilding TF-IDF → semantic_search returns results ✓

**Level 2 — Retrieval pipeline:**
- API still returns "only heading" despite semantic_search finding the file
- Root cause: `_add_result` deduplicates by `source_path`. Data_Linkage.md has 5+ chunks.
  First chunk = heading. All subsequent body chunks killed by dedup.
- Fix: read full file body after TF-IDF discovery, not chunk-level snippets

**Level 3 — Already addressed** (Data_Linkage.md Wiki entry created)

**Level 4 — API layer:**
- ehds_kg API server had no `/api/retrieve` endpoint → added
- edm_home EHDSKGRetriever still reading files directly → refactored to HTTP client
- Cloudflare tunnel: paths forward correctly, no configuration needed

### Key Insight
The chunk-dedup bug is subtle because it produces results that LOOK correct
(sources list shows Data_Linkage.md) but are CONTENT-WRONG (text is just the heading).
Always check the actual text length and content of retrieved results, not just
that results exist.
