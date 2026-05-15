# Hermes Agent Migration & MCP Integration

Session reference: 2026-05-10. Cross-machine migration of a fully-configured
Hermes Agent instance, plus exposing its knowledge base as an MCP server to
external clients (Claude Desktop, Cursor, LangChain, Agno).

---

## 1. Pack / Restore Migration Pattern

When moving a Hermes Agent installation to a new machine, you need both the
source code AND the runtime state (sessions, config, skills, knowledge bases).

### What to pack

| Source | Why |
|--------|-----|
| `~/.hermes/hermes-agent/` | Source code (tools, gateway, CLI, tests) |
| `~/.hermes/docs/ehds_kb/` | Project knowledge base (Markdown) |
| `~/.hermes/docs/ehds_wiki/` | Project wiki (Markdown) |
| `~/.hermes/drive_ehds_docs*` | Raw documents (PDF) |
| `~/.hermes/sessions/` | Conversation history |
| `~/.hermes/state.db` | SQLite session store |
| `~/.hermes/config.yaml` | Main configuration |
| `~/.hermes/auth.json` | OAuth tokens / credential pools |

### Pack script (`pack.sh`)

```bash
#!/bin/bash
set -e
BACKUP_DIR="/home/$(whoami)/migration_backup"
S_HOME="/home/$(whoami)/.hermes"
S_AGENT="$S_HOME/hermes-agent"

mkdir -p "$BACKUP_DIR"

# 1. Source code
tar -czf "$BACKUP_DIR/hermes_agent_src.tar.gz" -C "$S_AGENT" .

# 2. State (KB + sessions + critical files)
STATE_TMP="$BACKUP_DIR/state_tmp"
mkdir -p "$STATE_TMP"
for target in docs/ehds_kb docs/ehds_wiki drive_ehds_docs drive_ehds_docs_r1 drive_ehds_docs_r2 sessions; do
    if [ -d "$S_HOME/$target" ]; then
        cp -r "$S_HOME/$target" "$STATE_TMP/"
    fi
done
cp "$S_HOME/state.db" "$STATE_TMP/" 2>/dev/null || true
cp "$S_HOME/config.yaml" "$STATE_TMP/" 2>/dev/null || true
cp "$S_HOME/auth.json" "$STATE_TMP/" 2>/dev/null || true

tar -czf "$BACKUP_DIR/hermes_state.tar.gz" -C "$STATE_TMP" .
rm -rf "$STATE_TMP"
```

### Restore script (`awakening.sh`)

```bash
#!/bin/bash
set -e
NEW_HERMES_HOME="/home/$(whoami)/.hermes"
BACKUP_SOURCE="."

export HERMES_HOME="$NEW_HERMES_HOME"
echo "export HERMES_HOME=$NEW_HERMES_HOME" >> ~/.bashrc

mkdir -p "$NEW_HERMES_HOME"
tar -xzf "$BACKUP_SOURCE/hermes_state.tar.gz" -C "$NEW_HERMES_HOME"
mkdir -p "$NEW_HERMES_HOME/hermes-agent"
tar -xzf "$BACKUP_SOURCE/hermes_agent_src.tar.gz" -C "$NEW_HERMES_HOME/hermes-agent"

cd "$NEW_HERMES_HOME/hermes-agent"
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env"
fi
uv sync

sudo chown -R "$(whoami)" "$NEW_HERMES_HOME"
```

After restore, run `source ~/.bashrc` and restart any gateway service.

---

## 2. MCP Architecture: Client vs Server

Hermes Agent has **two entirely separate MCP code paths**. Do not confuse them.

### Path A: MCP Client (`tools/mcp_tool.py`)

- **Role**: Hermes connects TO external MCP servers
- **Config**: `~/.hermes/config.yaml` → `mcp_servers:`
- **Usage**: Hermes discovers external tools and calls them
- **Starts via**: `discover_mcp_tools()` at agent startup
- **Never** expose this file to Claude Desktop / Cursor as a server entrypoint

### Path B: Hermes as MCP Server (`mcp_serve.py`)

- **Role**: Exposes Hermes messaging conversations as MCP tools
- **Starts via**: `hermes mcp serve` (stdio server)
- **Tools**: `conversations_list`, `messages_read`, `messages_send`, etc.
- **Client config**:
  ```json
  {"mcpServers": {"hermes": {"command": "hermes", "args": ["mcp", "serve"]}}}
  ```

### Pitfall: Using `mcp_tool.py` as a Server

A common mistake is pointing Claude Desktop's `claude_desktop_config.json` at
`tools/mcp_tool.py`. This file has no `FastMCP` server object and no stdio
server loop. It will exit immediately or hang. The correct approach depends on
what you want:

| Goal | Correct file |
|------|-------------|
| Hermes reads external MCP tools | `config.yaml` + `mcp_servers:` |
| External client reads Hermes conversations | `mcp_serve.py` via `hermes mcp serve` |
| External client reads Hermes KB/docs | Custom FastMCP server (see §3) |

---

## 3. Knowledge Base as MCP Server (FastMCP)

To expose a local knowledge base (markdown + PDF) to any MCP client, create a
dedicated FastMCP server script. This is **not** built into Hermes; you write it
as a standalone Python file.

### Minimal KB MCP Server template

```python
#!/usr/bin/env python3
"""FastMCP server exposing a local knowledge base."""
from mcp.server.fastmcp import FastMCP
from pathlib import Path
import json, os

KB_ROOTS = [Path(os.environ.get("HERMES_HOME", "~/.hermes")) / "docs" / "ehds_kb"]
mcp = FastMCP("paperclip-ehds")

@mcp.tool()
def list_documents() -> str:
    docs = []
    for root in KB_ROOTS:
        for p in root.rglob("*.md"):
            docs.append({"path": str(p.relative_to(root)), "size": p.stat().st_size})
    return json.dumps(docs, indent=2)

@mcp.tool()
def read_document(path: str) -> str:
    for root in KB_ROOTS:
        target = (root / path).resolve()
        try:
            target.relative_to(root.resolve())
            if target.exists() and target.suffix == ".md":
                return target.read_text(encoding="utf-8", errors="replace")
        except ValueError:
            pass
    return f"[ERROR] Not found or outside KB: {path}"

@mcp.tool()
def search_kb(query: str, max_results: int = 20) -> str:
    keywords = [k for k in query.strip().split() if k]
    matches = []
    for root in KB_ROOTS:
        for p in root.rglob("*.md"):
            text = p.read_text(encoding="utf-8", errors="replace").lower()
            if all(k.lower() in text for k in keywords):
                matches.append({"path": str(p.relative_to(root)), "snippet": text[:500]})
            if len(matches) >= max_results:
                break
    return json.dumps({"query": query, "matches": matches}, indent=2)

if __name__ == "__main__":
    mcp.run()  # stdio transport
```

### Client config (Claude Desktop)

```json
{
  "mcpServers": {
    "paperclip-ehds": {
      "command": "uv",
      "args": ["run", "python", "/home/<user>/.hermes/ehds_mcp_server.py"],
      "env": {"HERMES_HOME": "/home/<user>/.hermes"}
    }
  }
}
```

### Security checklist for KB servers

- [ ] Path traversal guard (`relative_to()` check)
- [ ] Symlink outside root rejected
- [ ] File size cap (e.g. 5 MB)
- [ ] PDF parsing timeout (e.g. 15 s)
- [ ] No secrets in `args` array (use `env` instead)

### PDF extraction fallback chain

1. `pymupdf` (best) → `pip install pymupdf`
2. `pdftotext` (poppler-utils) → `apt install poppler-utils`
3. Return error instructing user to install one of the above

---

## 4. Fast check after restore

```bash
# Verify Hermes CLI
hermes doctor

# Verify MCP server standalone
fastmcp inspect ~/.hermes/ehds_mcp_server.py:mcp
fastmcp call ~/.hermes/ehds_mcp_server.py:list_documents --json

# Reload MCP in a running Hermes session
/reload-mcp
```
