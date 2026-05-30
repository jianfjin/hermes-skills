# MCP Server Protocol Pitfalls for Hermes Tool Injection

## Problem

An MCP server was built (`scripts/eventbus_mcp_server.py`) to expose `publish_event`, `subscribe_events`, and `event_bus_status` as Hermes-native tools. The server started (was spawned by the gateway) but its tools were never injected into any agent session.

## Root Cause: `tools/list` Response Format

The MCP protocol (JSON-RPC 2.0) requires the `tools/list` result to be an **object** with a `tools` key:

```json
// CORRECT:
{"jsonrpc": "2.0", "id": 1, "result": {"tools": [{"name": "x", ...}]}}

// WRONG:
{"jsonrpc": "2.0", "id": 1, "result": [{"name": "x", ...}]}
```

The wrong format produces this gateway log error:
```
ValidationError: 4 validation errors for JSONRPCMessage
  Input should be an object [type=dict_type, input_value=[{...}, ...], input_type=list]
```

**In Python:**
```python
# WRONG — sends the tools array directly:
def handle_list_tools(request_id):
    send_result(request_id, TOOLS)  # TOOLS is a list

# CORRECT — wraps in an object:
def handle_list_tools(request_id):
    send_result(request_id, {"tools": TOOLS})
```

## The `send_result` Function

When building an MCP server from scratch (no SDK), the standard response helper:

```python
def send_result(request_id, result):
    print(json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result}), flush=True)
```

This helper is agnostic about the result shape — whatever you pass as `result` becomes the JSON-RPC result field. The protocol contract is defined by the method:

| Method | Result shape | Example |
|--------|-------------|---------|
| `initialize` | `{"protocolVersion": ..., "capabilities": ..., "serverInfo": ...}` | Object |
| `tools/list` | `{"tools": [{"name": ..., "inputSchema": ...}]}` | Object with `tools` array |
| `tools/call` | `{"content": [{"type": "text", "text": "..."}]}` | Object with `content` array |

## Tool Name Prefixing

Hermes prefixes MCP tool names with `mcp_{server_name}_{tool_name}`. The server in `mcp_servers` config key is the server name:

```yaml
mcp_servers:
  eventbus:  # <-- this becomes the prefix
    command: "python3"
    args: [...]
```

Tools registered from this server are named `mcp_eventbus_publish_event`, `mcp_eventbus_subscribe_events`, etc.

## Environment Inheritance

MCP server subprocesses inherit a **filtered** environment from the Hermes gateway — only `PATH`, `HOME`, `USER`, `LANG`, `LC_ALL`, `TERM`, `SHELL`, `TMPDIR`, and `XDG_*` variables. All other env vars (API keys, tokens) are stripped unless explicitly added via the server config's `env:` block.

Critically, when running under a profile session (`hermes -p profile chat -q`), the gateway may pass the profile's `$HOME` as the gateway's `HOME`. This means `os.path.expanduser("~")` inside the MCP server resolves to the PROFILE'S home directory, not the user's real home.

**Fix:** Pass all shared resource paths as absolute paths, and set `HOME` explicitly:

```yaml
mcp_servers:
  eventbus:
    command: "python3"
    args: ["/absolute/path/to/server.py"]
    env:
      EVENT_BUS_DB_PATH: "/home/realuser/.hermes/shared/event_bus.db"
      HOME: "/home/realuser"
```

## Debugging Checklist

When an MCP server's tools don't appear in agent sessions:

1. **Is the server process running?** `ps aux | grep <server_name>`. If not visible:
   - Check `~/.hermes/logs/mcp-stderr.log` for startup errors
   - Check `journalctl --user -u hermes-gateway.service` for MCP connection errors
   - Look for `ValidationError` in logs (usually the `tools/list` format bug)
2. **Is the server registered?** `hermes tools list | grep <server_name>` — yes means gateway knows it
3. **Are tools injected?** Ask a fresh agent session to list all tools and grep for `mcp_<server>_`
4. **Restart gateway?** Config changes (new/removed servers) require `systemctl --user restart hermes-gateway.service`
5. **Try raw protocol test:**
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python3 /path/to/server.py
   ```
