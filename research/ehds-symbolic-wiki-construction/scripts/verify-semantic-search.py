#!/usr/bin/env python3
"""
verify-semantic-search.py
=========================
Quick end-to-end probe for the EHDS semantic search pipeline.
Run after `ehds_embedding.py --build` and after starting the API server.

Usage:
    python3 verify-semantic-search.py

Exit code 0 = all probes passed.
Exit code 1 = at least one probe failed.
"""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
API_BASE = "http://127.0.0.1:8080"
PROBES: list[dict] = []


def record(name: str, passed: bool, detail: str = ""):
    PROBES.append({"name": name, "passed": passed, "detail": detail})
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))


def main():
    print("[*] Probing EHDS Semantic Search Pipeline...")
    failed = False

    # 1. TF-IDF artifacts exist
    db_exists = (HERMES_HOME / "docs" / "ehds_embeddings.db").exists()
    pkl_exists = (HERMES_HOME / "docs" / "ehds_tfidf.pkl").exists()
    record(
        "TF-IDF artifacts exist",
        db_exists and pkl_exists,
        f"db={db_exists}, pkl={pkl_exists}",
    )
    if not (db_exists and pkl_exists):
        print("[!] Run: python3 ehds_embedding.py --build")
        failed = True

    # 2. API health
    try:
        with urllib.request.urlopen(f"{API_BASE}/api/health", timeout=5) as resp:
            data = json.loads(resp.read())
            healthy = data.get("status") == "healthy"
            record("API health check", healthy)
            if not healthy:
                failed = True
    except Exception as exc:
        record("API health check", False, str(exc))
        failed = True

    # 3. Stack counts
    try:
        with urllib.request.urlopen(f"{API_BASE}/api/stack", timeout=5) as resp:
            data = json.loads(resp.read())
            index_count = data["layers"]["index"]["file_count"]
            record("Index layer count > 0", index_count > 0, f"count={index_count}")
    except Exception as exc:
        record("Index layer count", False, str(exc))
        failed = True

    # 4. Semantic search returns results
    try:
        url = f"{API_BASE}/api/semantic_search?q=HDAB+approval&top_k=3"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
            match_count = data.get("match_count", 0)
            record("Semantic search returns matches", match_count > 0, f"matches={match_count}")
            if match_count == 0:
                failed = True
    except Exception as exc:
        record("Semantic search returns matches", False, str(exc))
        failed = True

    # 5. Citation resolution still works
    try:
        url = f"{API_BASE}/api/resolve?citation=Art.54(2)"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            found = data.get("found", False)
            record("Citation resolution", found, f"stable_id={data.get('stable_id')}")
            if not found:
                failed = True
    except Exception as exc:
        record("Citation resolution", False, str(exc))
        failed = True

    # Summary
    print("\n" + "=" * 50)
    total = len(PROBES)
    passed = sum(1 for p in PROBES if p["passed"])
    print(f"RESULTS: {passed}/{total} probes passed")
    if failed:
        print("[!] Semantic search pipeline is NOT ready.")
        sys.exit(1)
    else:
        print("[+] Semantic search pipeline is ready.")
        sys.exit(0)


if __name__ == "__main__":
    main()
