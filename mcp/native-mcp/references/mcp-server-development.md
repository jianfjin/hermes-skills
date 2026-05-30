# MCP Server Development Patterns

Lessons from building a stdio-based MCP server for the inter-agent event bus.

## Protocol Basics

MCP uses JSON-RPC 2.0 over stdin/stdout. The server reads one JSON object per line from stdin, processes it, and writes one JSON object per line to stdout.

## Critical: `tools/list` Response Format

The response to `tools/list` MUST wrap the tool array in an object:

```json
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "foo", ...}]}}
```

NOT:

```json
{"jsonrpc": "2.0", "id": 1, "result": [{"name": "foo", ...}]}
```

The symptom: `pydantic_core.ValidationError: Input should be an object` — scrolled off in gateway logs, easy to miss. The gateway registers the server (`hermes tools list` shows `all tools enabled`), but session agents see zero MCP tools from this server.

## `tools/call` Response Format

```json
{"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": "..."}]}}
```

MCP supports multiple content blocks per response. Type `text` is the most common.

## Connection Lifecycle

1. `initialize` — exchange protocol version + capabilities
2. `notifications/initialized` — client signals readiness (no response expected)
3. `tools/list` — client discovers tools
4. `tools/call` — client invokes a tool (repeated as needed)
5. stdin EOF — server exits cleanly

The Hermes gateway spawns the MCP server as a subprocess. If the server exits before the gateway is done, tools are silently unavailable. Use `tail -f ~/.hermes/logs/mcp-stderr.log` to see server start/stop events.

## Environment Isolation

The Hermes gateway passes a FILTERED environment to MCP subprocesses. Only safe baseline variables (PATH, HOME, USER, LANG, etc.) and explicitly configured `env:` entries are forwarded.

**Critical for cross-profile resources:** If an MCP server accesses files via `~` or `$HOME`, the path will resolve to the profile's home directory (`~/.hermes/profiles/<name>/home/`) — NOT the real user home. Workarounds:

```yaml
mcp_servers:
  myserver:
    command: "python3"
    args: ["/path/to/server.py"]
    env:
      SHARED_DB_PATH: "/home/realuser/.hermes/shared/db.db"
      HOME: "/home/realuser"
```

## Server Not Showing Tools in Session

If `hermes tools list` shows your server as "all tools enabled" but the agent session has zero MCP tools from it:

1. **Check the log:** `grep -i 'mcp\|validation\|jsonrpc' ~/.hermes/logs/mcp-stderr.log` and `journalctl --user -u hermes-gateway.service`
2. **Verify `tools/list` format** — the array-inside-object requirement is the #1 cause
3. **Verify stdin read** — the server must read lines from stdin in a loop, not just handle one request then exit
4. **Restart after config change** — `systemctl --user restart hermes-gateway.service`

## Minimal Viable Server Template

```python
#!/usr/bin/env python3
"""Minimal MCP stdio server — one tool, one call."""
import json, sys

TOOLS = [{
    "name": "ping",
    "description": "Simple health check — returns pong",
    "inputSchema": {"type": "object", "properties": {}},
}]

def send(id, data):
    print(json.dumps({"jsonrpc": "2.0", "id": id, "result": data}), flush=True)

for line in sys.stdin:
    msg = json.loads(line.strip())
    method, params, msgid = msg["method"], msg.get("params", {}), msg.get("id")
    if method == "initialize":
        send(msgid, {"protocolVersion": "2024-11-05", "capabilities": {},
                     "serverInfo": {"name": "minimal-mcp", "version": "1.0"}})
    elif method == "tools/list":
        send(msgid, {"tools": TOOLS})          # ← MUST be wrapped object
    elif method == "tools/call":
        send(msgid, {"content": [{"type": "text", "text": "pong"}]})
    elif method == "notifications/initialized":
        pass  # no response needed
```
