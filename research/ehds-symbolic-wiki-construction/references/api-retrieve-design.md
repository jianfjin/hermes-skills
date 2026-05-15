# /api/retrieve — Three-Layer Retrieval Contract

Design rationale and implementation pattern for the EHDS KG REST API
retrieval endpoint. Extracted from the 2026-05-12 Inner Circle debate
and Linus/Xiaolong/Jobs architecture review.

## Design Principle

**One endpoint, one responsibility.** The server owns the data and the
retrieval logic. Clients compose nothing — they ask for what they need
and the server does the work. This prevents distributed-monolith decay
where orchestration logic duplicates across services.

## Endpoint

```
GET /api/retrieve?q=<query>&depth=<0|1|2>&max_results=<1-20>
```

## Depth Levels

| depth | Layers | Latency | What it does |
|-------|--------|---------|-------------|
| 0 | Index only | <5ms | Citation lookup + token-based keyword match against 37 legal articles |
| 1 | Index + Wiki + KB | ~50ms | depth=0 + TF-IDF semantic search across 604 chunks (5000 vocab, cosine similarity) |
| 2 | Full stack | ~100ms | depth=1 + compliance audit (EHDS-SEC-* rules, severity scoring) |

## Response Contract

```json
{
  "query": "data linkage in EHDS",
  "depth": 1,
  "result_count": 3,
  "results": [
    {
      "layer": "wiki",
      "document": "EHDS-Wiki",
      "section": "ehds_wiki/Data_Linkage.md",
      "similarity": 0.72,
      "text": "# Data Linkage in EHDS\n\n## Definition...",
      "source_path": "ehds_wiki/Data_Linkage.md",
      "article": "66, 68"
    }
  ]
}
```

## Error Handling

- Missing `q` → 400 `{"error": "Missing q"}`
- No matches → 200 with `result_count: 0` and empty `results[]`
- TF-IDF engine uninitialized → depth>=1 silently omitted (no error, just fewer results)
- Invalid depth → clamped to 0-2 range
- API unreachable → consumer returns empty context (logs warning)

## Implementation Pattern

### Server side (ehds_api_server.py)

```python
if path == "/api/retrieve":
    query = q.get("q", [""])[0]
    depth = max(0, min(2, int(q.get("depth", ["1"])[0])))
    max_results = min(int(q.get("max_results", ["5"])[0]), 20)
    
    results = []
    # depth>=0: token-based Index match
    # depth>=1: lazy-import embed engine, semantic_search()
    # depth>=2: audit_document()
    
    return self._json({"query": query, "depth": depth, 
                       "result_count": len(results[:max_results]),
                       "results": results[:max_results]})
```

### Client side (edm_home EHDSKGRetriever)

```python
class EHDSKGRetriever:
    def __init__(self, api_url="http://localhost:8080"):
        self._api_url = api_url
    
    def retrieve(self, query, depth=1, max_results=5):
        params = urllib.parse.urlencode({"q": query, "depth": depth, 
                                          "max_results": max_results})
        url = f"{self._api_url}/api/retrieve?{params}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read())
        # Build context text for LLM prompt
        parts = [f"[EHDS-{r['layer'].upper()}] {r['section']}\n{r['text'][:600]}" 
                 for r in data.get("results", [])]
        return ("\n\n".join(parts), data.get("results", []))
```

## Key Design Decisions

1. **Read full file body, not chunk snippets.** The TF-IDF engine is for *discovery*
   (which file matches), not *content extraction* (what text to send). Chunk-level
   `text` from `semantic_search()` is a single paragraph fragment — often just the
   heading. After discovery, read the full source file (strip YAML frontmatter, cap
   at 800 chars) for rich LLM context.

2. **Token-based, not substring, matching for Index layer.** "Art 5" must not match
   "Art 50". Use `re.findall(r"[a-z0-9]+", query)` to tokenize, then require all tokens
   in article text.

3. **Lazy engine singleton.** The TF-IDF engine loads a 16MB SQLite at init. Import
   inside the handler, not at module level — avoids blocking server startup.

4. **Internal calls use localhost, not Cloudflare tunnel.** Same-VM service-to-service
   calls go to `http://localhost:8080`. The Cloudflare tunnel (wiki.edmf.nl) is for
   browser users. Internal calls through the tunnel add 50-100ms latency and an
   unnecessary external dependency.

## Related

- SKILL.md: "Expanded API Endpoints (Phase 2)" — endpoint listing
- SKILL.md: "Chunk Dedup Kills Body Text" — why we read full files
- SKILL.md: "Index Substring Matching" — why we tokenize
- `ehds_api_server.py` — reference implementation
