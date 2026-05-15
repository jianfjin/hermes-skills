# /api/retrieve — API Contract

Single endpoint for EHDS knowledge graph retrieval. Composes all three layers
(citation resolution, semantic search, audit rules) behind one HTTP call.

## Request

```
GET /api/retrieve?q=<query>&depth=<0|1|2>&max_results=<1-20>
```

| Param | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `q` | string | (required) | — | Search query or citation string |
| `depth` | int | 1 | 0–2 | Retrieval depth level |
| `max_results` | int | 5 | 1–20 | Max results returned |

Invalid params are silently clamped (no 400 for out-of-range values).

## Depth Levels

| Depth | Name | What it does | Latency |
|-------|------|-------------|---------|
| 0 | Citation | Token-based match against Index stable_ids, titles, and body text | <5ms |
| 1 | Semantic | Depth-0 + TF-IDF cosine similarity across all 3 layers (604 chunks, vocab=5000). Reads full file body for rich context. | <50ms |
| 2 | Audit | Depth-1 + compliance audit rules (EHDS-SEC-*) against the query or matched documents | <100ms |

If a layer's dependency is unavailable (no scikit-learn, no audit engine), that
layer returns empty — the request succeeds with whatever layers work.

## Response (200 OK)

```json
{
  "query": "explain data linkage in EHDS",
  "depth": 1,
  "result_count": 1,
  "results": [
    {
      "layer": "wiki",
      "document": "EHDS-Wiki",
      "section": "Data Linkage in EHDS",
      "similarity": 0.72,
      "text": "# Data Linkage in EHDS\n\n## Definition (ISO 5127:2017)...",
      "source_path": "ehds_wiki/Data_Linkage.md",
      "article": "66, 68"
    }
  ]
}
```

### Result Fields by Layer

| Field | Index (depth=0) | Wiki/KB (depth≥1) | Audit (depth=2) |
|-------|-----------------|-------------------|-----------------|
| `layer` | "index" | "wiki" or "kb" | "audit" |
| `document` | "EHDS-Index-54" | "EHDS-Wiki" / "EHDS-Kb" | "EHDS-Audit" |
| `section` | Article title | Wiki entry title or path | "[CRITICAL] RULE_ID" |
| `similarity` | — | Cosine score (0–1) | — |
| `text` | Body[:800] | Full body[:800] | "description\nremediation" |
| `source_path` | "ehds_index/Art-054.md" | "ehds_wiki/Data_Linkage.md" | "edm_home_query" |
| `stable_id` | "EHDS-2025-327-A54" | — | — |
| `article` | — | Article numbers from frontmatter | — |
| `rule_id` | — | — | "EHDS-SEC-LINK-001" |
| `severity` | — | — | "critical"/"high"/"medium" |

## Error Responses

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Missing `q` parameter | `{"error": "Missing q"}` |
| 200 | No matches found | `{"query": "...", "depth": N, "result_count": 0, "results": []}` |
| 200 | TF-IDF engine unavailable | Depth-0 results only, depth≥1 silently omitted |

No matches is not an error — it's a valid response indicating the KG has no
content for this query.

## Consumer Integration

The consumer builds its LLM prompt from the `text` fields:

```python
context = "\n\n".join(
    f"[EHDS-{r['layer'].upper()}] {r.get('section','')}\n{r.get('text','')[:600]}"
    for r in data["results"]
)
```

This produces a markdown-formatted context block ready for prompt injection.

## CORS

All responses include `Access-Control-Allow-Origin: *`. No additional
configuration needed for browser-based consumers or Cloudflare tunnels.
