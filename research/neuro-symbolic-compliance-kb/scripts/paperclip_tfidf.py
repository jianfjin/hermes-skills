"""
Paperclip TF-IDF Semantic Layer — Lightweight hybrid retrieval for EHDS compliance.

Design: ~100 lines (Linus spec). Singleton. No external DB.
Builds on neuro-symbolic-compliance-kb Phase 2 patterns.
Falls back to TF-IDF when neural embeddings are unavailable (≤2GB RAM VMs).

Usage:
    from paperclip_tfidf import get_engine
    engine = get_engine(kb_roots=["ehds_index/", "ehds_wiki/"])
    results = engine.search("HDAB approval requirements", top_k=5)
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ── Singleton ──────────────────────────────────────────────────────────
_engine_instance: PaperclipTFIDF | None = None


def get_engine(kb_roots: list[str] | None = None, force_rebuild: bool = False) -> "PaperclipTFIDF":
    global _engine_instance
    if _engine_instance is None or force_rebuild:
        _engine_instance = PaperclipTFIDF(kb_roots or ["ehds_index/", "ehds_wiki/"])
    return _engine_instance


# ── Engine ─────────────────────────────────────────────────────────────
class PaperclipTFIDF:
    def __init__(self, kb_roots: list[str], cache_path: str = "~/.hermes/cache/paperclip_tfidf.pkl"):
        self.kb_roots = [Path(p).expanduser().resolve() for p in kb_roots]
        self.cache_path = Path(cache_path).expanduser()
        self.vectorizer: TfidfVectorizer | None = None
        self.chunk_matrix: np.ndarray | None = None          # shape: (n_chunks, n_features) sparse
        self.chunk_metadata: list[dict[str, Any]] = []        # {path, article, title, layer}
        self._load_or_build()

    # ── Public API ─────────────────────────────────────────────────
    def search(self, query: str, top_k: int = 5, layer: str | None = None) -> list[dict[str, Any]]:
        """Semantic search across KB. Returns [{score, path, title, article, snippet}, ...]."""
        if self.vectorizer is None or self.chunk_matrix is None:
            return [{"error": "engine not built — run rebuild()"}]

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.chunk_matrix)[0]

        # Filter by layer if requested
        indices = range(len(scores))
        if layer:
            indices = [i for i, m in enumerate(self.chunk_metadata) if m.get("layer") == layer]

        ranked = sorted(
            [(i, scores[i]) for i in indices if scores[i] > 0],
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        return [
            {
                "score": round(float(score), 4),
                "path": str(self.chunk_metadata[i]["path"]),
                "title": self.chunk_metadata[i].get("title", ""),
                "article": self.chunk_metadata[i].get("article", ""),
                "layer": self.chunk_metadata[i].get("layer", "unknown"),
                "snippet": self._get_snippet(i),
            }
            for i, score in ranked
        ]

    def rebuild(self) -> int:
        """Re-scan all KB roots and rebuild TF-IDF matrix. Returns chunk count."""
        return self._build_index()

    def stats(self) -> dict[str, Any]:
        return {
            "chunks": len(self.chunk_metadata),
            "features": int(self.chunk_matrix.shape[1]) if self.chunk_matrix is not None else 0,
            "kb_roots": [str(r) for r in self.kb_roots],
            "cache": str(self.cache_path) if self.cache_path.exists() else None,
        }

    # ── Internal ───────────────────────────────────────────────────
    def _load_or_build(self):
        if self.cache_path.exists():
            try:
                with open(self.cache_path, "rb") as f:
                    data = pickle.load(f)
                self.vectorizer = data["vectorizer"]
                self.chunk_matrix = data["matrix"]
                self.chunk_metadata = data["metadata"]
                if self._staleness_check():
                    self._build_index()
                return
            except (pickle.UnpicklingError, KeyError, EOFError):
                pass  # Cache corrupt — rebuild
        self._build_index()

    def _staleness_check(self) -> bool:
        """Return True if any KB file is newer than cache."""
        cache_mtime = self.cache_path.stat().st_mtime
        for root in self.kb_roots:
            if not root.exists():
                continue
            for md_file in root.rglob("*.md"):
                if md_file.stat().st_mtime > cache_mtime:
                    return True
        return False

    def _build_index(self) -> int:
        """Scan KB roots, chunk by paragraph, build TF-IDF matrix."""
        chunks: list[str] = []
        self.chunk_metadata = []

        for root in self.kb_roots:
            if not root.exists():
                continue
            layer = root.name.replace("ehds_", "").replace("_", "-")  # "index", "wiki", "kb"
            for md_file in sorted(root.rglob("*.md")):
                text = md_file.read_text(encoding="utf-8")
                title, body = self._split_frontmatter(text)
                # Chunk by paragraph (## headings)
                paragraphs = [p.strip() for p in body.split("\n\n") if p.strip() and len(p) > 50]
                if not paragraphs:
                    paragraphs = [body[:2000]]  # fallback: first 2000 chars
                for para in paragraphs:
                    chunks.append(para)
                    self.chunk_metadata.append({
                        "path": str(md_file.relative_to(root.parent)),
                        "title": title,
                        "article": self._extract_article(title, body),
                        "layer": layer,
                        "full_text": para,
                    })

        if not chunks:
            self.vectorizer = TfidfVectorizer(stop_words="english")
            self.chunk_matrix = self.vectorizer.fit_transform(["placeholder kb empty"])
            self.chunk_metadata = []
            return 0

        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000, min_df=1, max_df=0.85)
        self.chunk_matrix = self.vectorizer.fit_transform(chunks)
        self._save_cache()
        return len(chunks)

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "matrix": self.chunk_matrix, "metadata": self.chunk_metadata}, f)

    def _get_snippet(self, idx: int, max_len: int = 200) -> str:
        text = self.chunk_metadata[idx].get("full_text", "")
        return text[:max_len] + ("..." if len(text) > max_len else "")

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[str, str]:
        """Split YAML frontmatter from body. Returns (title, body)."""
        title = ""
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                fm = parts[1]
                body = parts[2]
                for line in fm.split("\n"):
                    if line.strip().startswith("title:"):
                        title = line.split(":", 1)[1].strip().strip('"').strip("'")
        return title, body

    @staticmethod
    def _extract_article(title: str, body: str) -> str:
        """Extract article number from frontmatter or body."""
        for line in (body[:500] + title).split("\n"):
            if "article:" in line.lower():
                return line.split(":", 1)[1].strip().strip('"').strip("'")
            if "Art." in line:
                return line.split("Art.")[1].strip().split()[0].rstrip(".")
        return ""


# ── Quick test ────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    engine = get_engine()
    query = sys.argv[1] if len(sys.argv) > 1 else "HDAB secondary use consent"
    print(f"Search: {query}")
    print(f"Stats: {engine.stats()}")
    for r in engine.search(query, top_k=5):
        print(f"  [{r['layer']}] {r['score']:.3f} | {r['title'] or r['path']}")
