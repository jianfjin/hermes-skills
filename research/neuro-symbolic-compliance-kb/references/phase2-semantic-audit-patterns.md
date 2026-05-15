# Phase 2 Semantic Search & Audit Patterns

Session: EHDS Paperclip Phase 2 build (2026-05-11).
VM constraints: 2-core Intel Xeon 2.2 GHz, 1.9 GB RAM, ~189 MB free.

---

## 1. TF-IDF Fallback for Neural Embeddings

**Problem**: `sentence-transformers/all-MiniLM-L6-v2` loads successfully but `encode()` hangs indefinitely on 1.9 GB RAM VMs. No exception is raised; the process simply blocks in the tokenizer/model forward pass.

**Solution**: Replace with `sklearn.TfidfVectorizer` trained on the corpus itself. For legal text with heavy keyword overlap, cosine similarity on TF-IDF vectors yields relevant results in <50 ms.

**Implementation sketch**:
```python
from sklearn.feature_extraction.text import TfidfVectorizer

vectorizer = TfidfVectorizer(
    stop_words="english",
    lowercase=True,
    ngram_range=(1, 2),
    max_features=5000,
    min_df=1,
    max_df=1.0,
)
chunk_matrix = vectorizer.fit_transform(texts)
# Query
q_vec = vectorizer.transform([query])
scores = (chunk_matrix * q_vec.T).toarray().ravel()
```

**Persistence**: Cache `vectorizer` + `chunk_matrix` to a pickle file; load at startup. Also store per-chunk metadata in SQLite for filtering by `layer`.

---

## 2. PyMuPDF Structured Extraction for Audit Location

Use PyMuPDF to return text blocks with exact coordinates, enabling paragraph-level audit citations in PDFs.

```python
import fitz  # PyMuPDF

def read_pdf_file_structured(path: Path) -> List[Dict[str, Any]]:
    doc = fitz.open(str(path))
    blocks: List[Dict[str, Any]] = []
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        for block in page.get_text("blocks"):
            x0, y0, x1, y1, text, block_no, block_type = block
            if block_type == 0:  # text block
                blocks.append({
                    "page": page_num + 1,
                    "bbox": [round(x0, 2), round(y0, 2), round(x1, 2), round(y1, 2)],
                    "text": text.strip(),
                    "line_estimate": len(blocks) + 1,
                })
    return blocks
```

In the audit engine, pass a `locator_keyword` (e.g., `"scientific"` for an ethics-committee violation). The engine scans `pdf_blocks` for the keyword and injects `page` + `bbox` into the JSON-LD violation object.

---

## 3. BaseHTTPServer Single-Threaded Initialization Pitfall

**Problem**: Python's built-in `http.server.BaseHTTPServer` (and `HTTPServer`) handles one request at a time. If `get_engine()` or any heavy initialization is triggered lazily inside a request handler, the first request blocks the server forever and subsequent requests timeout.

**Reproduction**:
```python
# BAD — handler triggers model load
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        engine = get_engine()  # Blocks here; no other request can be accepted
        ...
```

**Fix**: Pre-load in `main()` before `serve_forever()`:
```python
def main():
    if _EMBED_OK:
        from ehds_embedding import get_engine
        get_engine()  # Warm-up happens here
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
```

If the pre-load itself is too slow for foreground startup, consider:
1. Running the server in a background thread/process.
2. Using `socketserver.ThreadingMixIn`:
```python
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass
```

---

## 4. HuggingFace Offline Mode

On isolated or rate-limited VMs, set `HF_HUB_OFFLINE=1` before importing `sentence_transformers` to prevent network HEAD requests from blocking startup.

```bash
export HF_HUB_OFFLINE=1
python3 ehds_api_server.py
```

This is especially important when the model is already cached (`~/.cache/huggingface/hub`) but the library still attempts to verify remote metadata.
