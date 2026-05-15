#!/usr/bin/env python3
"""
EHDS Semantic Embedding Engine — Template
=========================================
Production-ready TF-IDF semantic search with optional neural fallback.
Designed for resource-constrained VMs (2-core / 1-2GB RAM).

Usage:
    python3 ehds_embedding.py --build          # rebuild TF-IDF index
    python3 ehds_embedding.py --search "query" # semantic search

Integrates with ehds_mcp_server.py and ehds_api_server.py via get_engine().
"""

from __future__ import annotations

import argparse
import json
import os
import pickle
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
DB_PATH = HERMES_HOME / "docs" / "ehds_embeddings.db"
TFIDF_PATH = HERMES_HOME / "docs" / "ehds_tfidf.pkl"

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ehds_mcp_server as mcp


# ---------------------------------------------------------------------------
# Embedding Engine
# ---------------------------------------------------------------------------

class EHDSEmbeddingEngine:
    """TF-IDF based semantic search engine with sklearn."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH
        self.tfidf_path = TFIDF_PATH
        self.vectorizer: Any = None
        self.chunk_matrix: Any = None
        self._init_db()
        self._load_or_build_tfidf()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL,
                    layer TEXT NOT NULL,
                    text TEXT NOT NULL,
                    tfidf TEXT,
                    metadata TEXT
                )
            """)
            conn.commit()

    def _load_chunks(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute(
                "SELECT id, source_path, layer, text, tfidf, metadata FROM chunks ORDER BY id"
            )
            rows = []
            for row in cur.fetchall():
                rows.append({
                    "id": row[0], "source_path": row[1], "layer": row[2],
                    "text": row[3],
                    "tfidf": json.loads(row[4]) if row[4] else None,
                    "metadata": json.loads(row[5]) if row[5] else None,
                })
            return rows

    def _load_or_build_tfidf(self):
        if self.tfidf_path.exists():
            with open(self.tfidf_path, "rb") as f:
                cache = pickle.load(f)
            self.vectorizer = cache["vectorizer"]
            self.chunk_matrix = cache["chunk_matrix"]
            return
        self.build_index()

    def build_index(self):
        all_chunks: List[Dict[str, Any]] = []
        for layer, root_name in [("index", "ehds_index"),
                                  ("wiki", "ehds_wiki"),
                                  ("kb", "ehds_kb")]:
            root = HERMES_HOME / "docs" / root_name
            if not root.exists():
                continue
            for f in sorted(root.glob("*.md")):
                chunks = self._extract_chunks(f, layer)
                for c in chunks:
                    c["layer"] = layer
                    c["source_path"] = str(f.relative_to(HERMES_HOME))
                all_chunks.extend(chunks)

        if not all_chunks:
            print("[!] No chunks found – nothing to index.")
            return

        from sklearn.feature_extraction.text import TfidfVectorizer
        texts = [c["text"] for c in all_chunks]
        self.vectorizer = TfidfVectorizer(
            stop_words="english", lowercase=True,
            ngram_range=(1, 2), max_features=5000,
            min_df=1, max_df=1.0,
        )
        self.chunk_matrix = self.vectorizer.fit_transform(texts)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chunks")
            for i, c in enumerate(all_chunks):
                dense = self.chunk_matrix[i].toarray().tolist()[0]
                conn.execute(
                    "INSERT INTO chunks (source_path, layer, text, tfidf, metadata) VALUES (?, ?, ?, ?, ?)",
                    (c["source_path"], c["layer"], c["text"],
                     json.dumps(dense), json.dumps(c.get("metadata", {}))),
                )
            conn.commit()

        with open(self.tfidf_path, "wb") as f:
            pickle.dump({"vectorizer": self.vectorizer, "chunk_matrix": self.chunk_matrix}, f)

        print(f"[+] Indexed {len(all_chunks)} chunks, vocab={len(self.vectorizer.vocabulary_)}")

    def _extract_chunks(self, path: Path, layer: str) -> List[Dict[str, Any]]:
        text = path.read_text(encoding="utf-8", errors="replace")
        meta, body = mcp._parse_frontmatter(text)
        chunks: List[Dict[str, Any]] = []

        if layer == "index":
            import re
            paragraphs = re.split(r"\n## Para \d+\n", body)
            para_headers = re.findall(r"\n## (Para \d+)\n", body)
            for idx, para in enumerate(paragraphs):
                para = para.strip()
                if not para:
                    continue
                header = para_headers[idx - 1] if idx > 0 and (idx - 1) < len(para_headers) else "Preamble"
                chunks.append({
                    "text": f"{meta.get('title', '')}\n{header}\n{para}",
                    "metadata": {
                        "stable_id": meta.get("stable_id"),
                        "article": meta.get("article"),
                        "header": header,
                    },
                })
        else:
            for para in body.split("\n\n"):
                para = para.strip()
                if para and not para.startswith("[["):
                    chunks.append({
                        "text": f"{meta.get('title', '')}\n{para}",
                        "metadata": {
                            "wiki_id": meta.get("wiki_id"),
                            "article": meta.get("article"),
                        },
                    })
        return chunks

    def semantic_search(
        self, query: str, top_k: int = 5, layer_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if self.vectorizer is None or self.chunk_matrix is None:
            return []
        q_vec = self.vectorizer.transform([query])
        scores = (self.chunk_matrix * q_vec.T).toarray().ravel()
        chunks = self._load_chunks()
        results = []
        for i, chunk in enumerate(chunks):
            if layer_filter and chunk["layer"] != layer_filter:
                continue
            score = float(scores[i])
            if score <= 0:
                continue
            results.append({
                "similarity": round(score, 4),
                "source_path": chunk["source_path"],
                "layer": chunk["layer"],
                "text": chunk["text"][:280] + "..." if len(chunk["text"]) > 280 else chunk["text"],
                "metadata": chunk.get("metadata", {}),
            })
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]


# Global singleton — critical for API gateway performance
_engine_instance: Optional[EHDSEmbeddingEngine] = None


def get_engine() -> EHDSEmbeddingEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EHDSEmbeddingEngine()
    return _engine_instance


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--search", type=str)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    engine = EHDSEmbeddingEngine()
    if args.build:
        engine.build_index()
    elif args.search:
        for r in engine.semantic_search(args.search, top_k=args.top_k):
            print(f"sim={r['similarity']} | {r['layer']} | {r['source_path']}")
    else:
        parser.print_help()
