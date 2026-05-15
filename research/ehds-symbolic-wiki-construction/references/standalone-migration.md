# EHDS-KG Standalone Migration — Proven Procedure

How to extract the EHDS three-layer knowledge stack from `~/.hermes/docs/` into a
standalone `~/projects/ehds_kg/` project that runs without Hermes MCP dependencies.

Successfully executed 2026-05-12. VM: 2-core, 1.9GB RAM, Python 3.11.

## Target Structure

```
~/projects/ehds_kg/
├── ehds_index/          # Layer 1 — 37 Articles
├── ehds_wiki/           # Layer 2 — 8 Wiki entries
├── ehds_kb/             # Layer 3 — 2 KB rules
├── src/
│   ├── __init__.py
│   ├── ehds_common.py   # ALL shared utilities (replaces ehds_mcp_server)
│   ├── ehds_embedding.py
│   ├── ehds_api_server.py
│   ├── batch_import.py
│   └── paperclip_tfidf.py
├── scripts/
│   ├── test_e2e.py
│   └── verify-semantic-search.py
├── data/source_pdfs/
├── cache/
├── dashboard/
└── docs/
```

## Step 1: Create Directories

```bash
mkdir -p ~/projects/ehds_kg/{ehds_index,ehds_wiki,ehds_kb,src,scripts,data/source_pdfs,cache,dashboard,docs/project_logs}
```

## Step 2: Copy Three Layers (exclude .bak files)

```bash
cp ~/.hermes/docs/ehds_index/*.md ~/projects/ehds_kg/ehds_index/
cp ~/.hermes/docs/ehds_wiki/*.md ~/projects/ehds_kg/ehds_wiki/
cp ~/.hermes/docs/ehds_kb/*.md ~/projects/ehds_kg/ehds_kb/
cp ~/.hermes/docs/ehds_audit/THREE_LAYER_ARCHITECTURE.md ~/projects/ehds_kg/
rm -f ~/projects/ehds_kg/ehds_index/*.bak
```

## Step 3: Copy Python Templates and Cache

```bash
# Templates → src/
cp ~/.hermes/skills/research/ehds-symbolic-wiki-construction/templates/ehds-embedding.py ~/projects/ehds_kg/src/
cp ~/.hermes/skills/research/ehds-symbolic-wiki-construction/templates/ehds-api-server.py ~/projects/ehds_kg/src/
cp ~/.hermes/skills/research/ehds-symbolic-wiki-construction/templates/batch-import.py ~/projects/ehds_kg/src/
cp ~/.hermes/skills/research/neuro-symbolic-compliance-kb/scripts/paperclip_tfidf.py ~/projects/ehds_kg/src/
# Scripts
cp ~/.hermes/skills/research/ehds-symbolic-wiki-construction/scripts/test_e2e.py ~/projects/ehds_kg/scripts/
cp ~/.hermes/skills/research/ehds-symbolic-wiki-construction/scripts/verify-semantic-search.py ~/projects/ehds_kg/scripts/
# Cache
cp ~/.hermes/docs/ehds_tfidf.pkl ~/projects/ehds_kg/cache/
cp ~/.hermes/docs/ehds_embeddings.db ~/projects/ehds_kg/cache/
```

## Step 4: Create `src/ehds_common.py` (THE CRITICAL STEP)

This replaces all `import ehds_mcp_server as mcp` references. Must contain:

- `PROJECT_ROOT` = two levels up from `src/ehds_common.py`
- Layer roots: `INDEX_ROOT`, `WIKI_ROOT`, `KB_ROOT`, `CACHE_ROOT`
- `_parse_frontmatter(text)` — try `yaml.safe_load`, fallback to simple parser
- `_load_index_entries()` — loads all Index .md files, cached for 300s
- `_resolve_citation(citation, index)` — 4-format resolver
- `_resolve_kb_path(user_path)` — safe path resolver with traversal guard
- `_walk_kb()` — enumerate all KB files
- `_read_text_file(path)`, `_read_pdf_file(path)`, `_read_pdf_file_structured(path)`
- `_search_in_file(path, keywords)` — full-text AND search
- `audit_document(path_str)` — 8 built-in rules incl. EHDS-SEC-LINK-001/002
- `_is_inside_roots(path)` — traversal guard

See the actual implementation at `~/projects/ehds_kg/src/ehds_common.py`.

## Step 5: Fix Path References in Every Python File

| File | Change |
|------|--------|
| `ehds_embedding.py` | `HERMES_HOME` → `from ehds_common import PROJECT_ROOT, CACHE_ROOT`; `import ehds_mcp_server` → `from ehds_common import _parse_frontmatter`; `HERMES_HOME / "docs" / root_name` → direct layer roots |
| `ehds_api_server.py` | Full rewrite — import all shared funcs from `ehds_common`, replace all `HERMES_HOME / "docs" / ...` paths |
| `batch_import.py` | `HERMES_HOME` → `from ehds_common import INDEX_ROOT` |
| `paperclip_tfidf.py` | Default `cache_path` → `PROJECT_ROOT / "cache" / "paperclip_tfidf.pkl"`; default `kb_roots` → absolute paths from PROJECT_ROOT |
| `test_e2e.py` | `import ehds_mcp_server` → `from ehds_common import ...`; `HERMES_HOME` → `PROJECT_ROOT` |
| `verify-semantic-search.py` | `HERMES_HOME` → `Path(__file__).resolve().parent.parent`; all paths updated |

## Step 6: Fix Python 3.12+ F-String Issues

`batch_import.py` has two f-string problems:

1. **Backslash in f-string expression** (line 85 original): `{"\n\n".join(para_blocks)}` → assign `"\n\n"` to a variable first
2. **Escaped quotes in f-string** (line 67 original): `f"""...\"{var}\"..."""` → use a temp variable for the quote character

## Step 7: Verify

```bash
cd ~/projects/ehds_kg
python3 -c "
import sys; sys.path.insert(0,'src')
from ehds_common import _load_index_entries, _resolve_citation
index = _load_index_entries()
assert len(index) >= 36
assert _resolve_citation('Art. 54', index) is not None
"
```

Then rebuild TF-IDF:
```bash
python3 src/ehds_embedding.py --build
python3 src/ehds_embedding.py --search "data linkage in EHDS"
```

## Key Design Decisions

- **`PROJECT_ROOT` computed from `__file__`**, not from env var — makes the project self-contained
- **`ehds_common.py` is the single shared module** — no cyclic imports, no Hermes dependency
- **Cache paths inside project** (`cache/`) — not in `~/.hermes/`
- **`_parse_frontmatter` tries `yaml.safe_load` first**, falls back to simple string parser — handles environments without PyYAML
- **`_load_index_entries()` caches for 300s** — prevents re-reading 37 files on every citation resolve

## Step 8: Connect External Services via API (do NOT read files)

External consumers (edm_home, any RAG, web frontends) must call the KG via
`GET /api/retrieve` — never read `ehds_index/*.md` directly.

**Consumer-side HTTP client** (replaces filesystem EHDSKGRetriever):
```python
class EHDSKGRetriever:
    def __init__(self, api_url=None):
        import os
        self._api_url = api_url or os.environ.get(
            "EHDS_KG_API_URL", "http://localhost:8080"
        )
    def retrieve(self, query, depth=1, max_results=5):
        import urllib.request, urllib.parse, json
        params = urllib.parse.urlencode({
            "q": query, "depth": depth, "max_results": max_results
        })
        with urllib.request.urlopen(f"{self._api_url}/api/retrieve?{params}", timeout=30) as r:
            data = json.loads(r.read())
        context = "\n\n".join(...)  # build from data["results"]
        return context, data["results"]
```

Full API spec: `references/api-retrieve-spec.md`.
