# Authoring Custom stdio MCP Servers

This file documents how to wrap arbitrary Python functions as Hermes-native MCP tools. The technique was developed during the inter-agent-event-bus Phase 1 v2 project.

## Architecture

A stdio MCP server is a long-lived subprocess that reads JSON-RPC 2.0 requests from stdin and writes responses to stdout. Hermes spawns the process at startup, discovers its tools via `tools/list`, and makes them available in every conversation.

```
Hermes Agent (MCP client) ←→ stdin/stdout (JSON-RPC 2.0) ←→ Your Python script (MCP server)
```

## Minimal Protocol (4 Message Types)

| Method | When | Response |
|--------|------|----------|
| `initialize` | Startup | Server info + capabilities |
| `notifications/initialized` | After initialize | Ignore (no response) |
| `tools/list` | After initialize | Array of tool definitions with JSON Schema |
| `tools/call` | Per tool invocation | `{"content":[{"type":"text","text":"..."}]}` or error |

## Minimal Server Template

```python
#!/usr/bin/env python3
import json, sys, traceback

TOOLS = [{
    "name": "my_tool",
    "description": "What it does",
    "inputSchema": {"type":"object","properties":{
        "arg1": {"type":"string"},
        "arg2": {"type":"integer","default":10},
    },"required":["arg1"]},
}]

def send(m): print(json.dumps(m), flush=True)

for line in sys.stdin:
    line = line.strip(); 
    if not line: continue
    msg = json.loads(line)
    mid, method, params = msg.get("id"), msg.get("method"), msg.get("params", {})
    
    if method == "initialize":
        send({"jsonrpc":"2.0","id":mid,"result":{
            "protocolVersion": params.get("protocolVersion","2024-11-05"),
            "capabilities":{"tools":{}},
            "serverInfo":{"name":"my-server","version":"1.0.0"},
        }})
    elif method == "notifications/initialized":
        pass
    elif method == "tools/list":
        send({"jsonrpc":"2.0","id":mid,"result":TOOLS})
    elif method == "tools/call":
        try:
            result = my_business_logic(**params.get("arguments",{}))
            send({"jsonrpc":"2.0","id":mid,"result":{"content":[{"type":"text","text":str(result)}]}})
        except Exception as e:
            send({"jsonrpc":"2.0","id":mid,"error":{"code":-32000,"message":str(e)}})
```

## Real-World Example

See `~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus/scripts/eventbus_mcp_server.py` for a production MCP server that wraps `publish_event`, `subscribe_events`, and `event_bus_status` as native Hermes tools.

## Config.yaml Integration

```yaml
mcp_servers:
  myserver:
    command: "python3"
    args: ["/absolute/path/to/server.py"]
    env:
      # Profile sessions redirect $HOME — pass absolute paths explicitly
      HOME: "/home/realuser"
      SHARED_DB_PATH: "/home/realuser/.hermes/shared/event_bus.db"
    timeout: 30
```

## Pitfalls

### 1. Profile `$HOME` isolation

When a profile session triggers an MCP tool call, the subprocess inherits `$HOME` pointing to `~/.hermes/profiles/<name>/home/`. `os.path.expanduser("~")` resolves to the WRONG location. Fix: pass `HOME` and shared resource paths explicitly in `env:`.

### 2. Tools not appearing in agent session

If mcp tools don't appear in the agent's tool list:
- Gateway must be restarted after config change: `systemctl --user restart hermes-gateway.service`
- Check server process is running: `ps aux | grep <server-name>`
- MCP tools use `mcp_{server}_{tool}` naming (not bare tool name)
- Server must handle `notifications/initialized` (silently ignore, no response)

### 3. No MCP SDK needed

MCP servers don't require any pip packages. The protocol is pure JSON-RPC 2.0 over stdio — `sys.stdin`/`sys.stdout` are all you need.

### 4. Server is long-lived

Hermes keeps the server running for the gateway's lifetime. State (DB connections, file handles) persists between tool calls. Handle reconnection gracefully.
