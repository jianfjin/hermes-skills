---
name: sanitize-llm-file-writes
description: Prevent accidental injection of line numbers and metadata when writing files that were read using tool-based pagination (which prefixes lines with 'N|').
version: 1.0.0
author: Feng Ge
---

# Sanitize LLM File Writes

## Problem
When using tools like `read_file`, the output often includes line numbers (e.g., ` 1|content`). If the LLM takes this output and writes it back to a file using `write_file`, the line numbers are persisted as literal text, corrupting configuration files (like `.toml` or `.env`) and breaking CLI tools (like `uv` or `git`).

## Detection
- Files contain leading numbers and pipes (` 1|`).
- Tools like `uv` report `TOML parse error` or `Couldn't parse requirement`.
- `grep` or `cat` reveals repeated line numbering (e.g., ` 1| 1|[project]`).

## Solution: The "Pure Overwrite" Pattern

### 1. Avoid Edit-Read-Write Loops for Configs
For critical configuration files (`pyproject.toml`, `requirements.txt`, `.env`), avoid reading the file, modifying the string, and writing it back. Instead, define the **entire desired state** as a clean string literal in the code.

### 2. Mandatory Cleaning Regex
If you must modify an existing file, apply a strict cleaning pass to remove tool-injected line numbers before writing.

**Python Cleaning Logic:**
```python
import re

def clean_tool_output(content: str) -> str:
    lines = content.splitlines()
    cleaned = [re.sub(r'^\s*\d+\|', '', line) for line in lines]
    return "\n".join(cleaned)
```

### 3. Verification Step
After writing, always verify the first 5 lines using a raw `terminal` command (`head -n 5`) rather than `read_file` to ensure no metadata leaked into the file.

## Pitfalls
- **Sashimi-slicing:** Don't just remove the first occurrence of `\d+|`; use a global regex or a loop to handle nested pollution.
- **Empty Lines:** Be careful not to accidentally strip meaningful empty lines during the regex process.
