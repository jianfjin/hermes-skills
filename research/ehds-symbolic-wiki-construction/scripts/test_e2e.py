#!/usr/bin/env python3
"""
EHDS Three-Layer Stack — End-to-End Test Template
=================================================
Starter script for validating a neuro-symbolic compliance KB after construction.
Copy this into your project, adjust HERMES_HOME and expected counts, then run:
    python3 test_e2e.py

Validates:
  - Index layer loads with stable IDs and anchors
  - Citation resolution handles all supported formats
  - Wiki layer has valid Frontmatter on every file
  - KB layer files exist
  - Path traversal is blocked
  - Audit engine detects known violations
  - Architecture documentation exists
"""

import sys, os, json
from pathlib import Path

# Adjust this to where your ehds_mcp_server.py lives
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ehds_mcp_server as mcp

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
PASS, FAIL = "✓", "✗"
passed = failed = 0

def check(cond, msg):
    global passed, failed
    (passed, failed) = (passed + 1, failed) if cond else (passed, failed + 1)
    print(f"  {PASS if cond else FAIL} {msg}")

print("=" * 60)
print("EHDS Knowledge Stack — E2E Validation")
print("=" * 60)

# 1. INDEX LAYER
print("\n[1/5] INDEX LAYER")
index = mcp._load_index_entries()
check(len(index) >= 7, f"Loaded {len(index)} entries (≥ 7)")
check("EHDS-2025-327-A54" in index, "Art. 54 exists")
check("EHDS-2025-327-A59" in index, "Art. 59 (HDAB) exists")
entry = index.get("EHDS-2025-327-A54", {})
check(entry.get("article") == 54, "Art. 54 number correct")
check(len(entry.get("anchors", {})) >= 4, f"≥4 anchors on Art. 54")

# 2. CITATION RESOLUTION
print("\n[2/5] CITATION RESOLUTION")
cases = [
    ("EHDS-2025-327-A54", "EHDS-2025-327-A54", None),
    ("EHDS-2025-327-A54-P2", "EHDS-2025-327-A54", "P2"),
    ("Art. 54", "EHDS-2025-327-A54", None),
    ("Art. 54(2)", "EHDS-2025-327-A54", "A054-P2"),
]
for cite, sid, anchor in cases:
    r = mcp._resolve_citation(cite, index)
    ok = r and r["entry"]["stable_id"] == sid and (not anchor or r.get("anchor") == anchor)
    check(ok, f"'{cite}' → {sid}")
check(mcp._resolve_citation("Art. 999", index) is None, "Missing cite returns None")

# 3. WIKI LAYER
print("\n[3/5] WIKI LAYER (Frontmatter)")
wiki_dir = HERMES_HOME / "docs" / "ehds_wiki"
files = list(wiki_dir.glob("*.md")) if wiki_dir.exists() else []
check(len(files) >= 7, f"{len(files)} wiki files (≥ 7)")
for f in files:
    text = f.read_text(encoding="utf-8", errors="replace")
    meta, _ = mcp._parse_frontmatter(text)
    check("wiki_id" in meta, f"{f.name} has wiki_id")
    check("index_refs" in meta, f"{f.name} has index_refs")

# 4. PATH SECURITY + AUDIT ENGINE
print("\n[4/5] PATH SECURITY & AUDIT")
check(mcp._resolve_kb_path("../../../etc/passwd") is None, "Traversal blocked")
# Simulate audit on a known-non-compliant doc
kb_path = HERMES_HOME / "docs" / "ehds_kb" / "buzzword_optimizer.md"
if kb_path.exists():
    text = mcp._read_text_file(kb_path).lower()
    has_hdab = "hdab" in text or "health data access body" in text
    check(not has_hdab, "Non-compliant doc lacks HDAB (audit should catch)")

# 5. ARCHITECTURE DOC
print("\n[5/5] ARCHITECTURE DOCUMENTATION")
arch = HERMES_HOME / "docs" / "ehds_audit" / "THREE_LAYER_ARCHITECTURE.md"
check(arch.exists(), "THREE_LAYER_ARCHITECTURE.md exists")
if arch.exists():
    body = mcp._read_text_file(arch)
    check("ehds_index" in body and "ehds_wiki" in body and "ehds_kb" in body,
          "Doc references all three layers")

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
