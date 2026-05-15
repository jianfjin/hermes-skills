#!/usr/bin/env python3
"""
EHDS Batch Import Tool — Template
==================================
Splits a large markdown file containing multiple EHDS Articles into
individual Index files under docs/ehds_index/.

Usage:
    python3 batch_import.py regulation_source.md [--regulation "2025/327"] [--year 2025]
    python3 batch_import.py --generate-skeleton --overwrite

Each Article must be delimited by a header like:
    ## Article 33
    ## Art. 33
    # Article 34 — Title
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))
INDEX_ROOT = HERMES_HOME / "docs" / "ehds_index"


def slugify_article(num: int, year: int = 2025) -> str:
    return f"EHDS-{year}-327_Art-{num}"


def generate_index_file(
    article_num: int,
    title: str,
    body: str,
    regulation: str = "(EU) 2025/327",
    year: int = 2025,
    category: str = "Chapter V — Secondary Use",
    overwrite: bool = False,
) -> Path:
    stable_id = f"EHDS-{year}-327-A{article_num}"
    filename = f"{slugify_article(article_num, year)}.md"
    filepath = INDEX_ROOT / filename

    if filepath.exists() and not overwrite:
        print(f"[SKIP] {filename} already exists")
        return filepath

    # Build paragraphs with ## Para N headers + anchors
    paragraphs = body.strip().split("\n\n")
    para_blocks: List[str] = []
    para_idx = 1
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if para.startswith("#"):
            para_blocks.append(para)
            continue
        anchor_tag = f"[[A{article_num}-P{para_idx}]]"
        para_blocks.append(f"## Para {para_idx}\n{anchor_tag}\n\n{para}")
        para_idx += 1

    content = f"""---
stable_id: "{stable_id}"
regulation: "EHDS Reg. {regulation}"
article: {article_num}
title: "{title}"
category: "{category}"
anchors:
    {{}}
---

# Article {article_num} — {title}

## Index Summary
> **Stable ID:** `{stable_id}`  
> **Regulation:** {regulation}  
> **Article:** {article_num}  
> **Category:** {category}

{"\n\n".join(para_blocks)}

## Cross-References
- 
"""
    filepath.write_text(content, encoding="utf-8")
    print(f"[WRITE] {filename} ({len(content)} bytes)")
    return filepath


def split_source(text: str) -> List[Tuple[int, str, str]]:
    pattern = re.compile(
        r"^#{1,2}\s+(?:Article|Art\.)\s*(\d+)(?:\s*—\s*|\s+-\s+|\s+)(.*?)$",
        re.MULTILINE | re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    results: List[Tuple[int, str, str]] = []
    for i, match in enumerate(matches):
        num = int(match.group(1))
        title = match.group(2).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        results.append((num, title, text[start:end].strip()))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", help="Source markdown file with multiple Articles")
    parser.add_argument("--regulation", default="(EU) 2025/327")
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--category", default="Chapter V — Secondary Use")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--generate-skeleton", action="store_true",
                        help="Generate skeleton Articles 33-67 from known EHDS structure")
    args = parser.parse_args()

    INDEX_ROOT.mkdir(parents=True, exist_ok=True)

    if args.generate_skeleton:
        # Insert your skeleton articles here or load from a data structure
        print("[+] Generate skeleton mode — fill in the articles list before use")
        return

    if not args.source:
        parser.print_help()
        sys.exit(1)

    source_path = Path(args.source)
    text = source_path.read_text(encoding="utf-8", errors="replace")
    chunks = split_source(text)
    print(f"[+] Found {len(chunks)} Articles in {source_path}")

    for num, title, body in chunks:
        generate_index_file(
            article_num=num, title=title, body=body,
            regulation=args.regulation, year=args.year,
            category=args.category, overwrite=args.overwrite,
        )

    print(f"[+] Done. Total Articles: {len(list(INDEX_ROOT.glob('*.md')))}")


if __name__ == "__main__":
    main()
