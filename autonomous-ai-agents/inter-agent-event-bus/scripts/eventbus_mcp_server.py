#!/usr/bin/env python3
"""MCP server for inter-agent event bus (Phase 1 v2).

Exposes publish_event, subscribe_events, and event_bus_status as
native MCP tools that any Hermes agent can call directly.

Usage (stdio transport):
  python3 eventbus_mcp_server.py

Hermes config.yaml entry:
  mcp_servers:
    eventbus:
      command: "python3"
      args: ["~/.hermes/skills/.../scripts/eventbus_mcp_server.py"]
      timeout: 30
"""

import json
import os
import sys
import traceback

# Path setup
SKILL_DIR = os.path.expanduser("~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus")
TOOLS_DIR = os.path.join(SKILL_DIR, "tools")
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from publish_event import publish_event
from subscribe_events import subscribe_events
from event_bus_status import event_bus_status
from connection import EventBusWriter
from event_schema_v2 import run_migrations, SCHEMA_VERSION

DB_PATH = os.environ.get(
    "EVENT_BUS_DB_PATH",
    os.path.join(os.path.expanduser("~"), ".hermes", "shared", "event_bus.db"),
)


def ensure_db():
    """Auto-init/migrate DB on first use."""
    w = EventBusWriter(DB_PATH)
    if w.conn is None:
        w.connect()
    row = w.conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    if row[0] == 0:
        run_migrations(w)
    else:
        cur_ver = w.conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
        if cur_ver < SCHEMA_VERSION:
            run_migrations(w)
    # v1→v2 column migration
    try:
        cols = [c[1] for c in w.conn.execute("PRAGMA table_info(events)").fetchall()]
        if 'source_agent' not in cols:
            w.conn.execute("ALTER TABLE events RENAME TO events_v1_legacy")
            w.conn.execute("""CREATE TABLE events (
                event_id INTEGER PRIMARY KEY, source_agent TEXT NOT NULL,
                event_type TEXT NOT NULL, payload TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending','processing','processed','dead','archived')),
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                processed_at TEXT, retry_count INTEGER NOT NULL DEFAULT 0,
                max_retries INTEGER NOT NULL DEFAULT 3, error_message TEXT,
                ttl_seconds INTEGER DEFAULT 86400)""")
            w.conn.execute("""INSERT INTO events(event_id,source_agent,event_type,payload,status,created_at,ttl_seconds)
                SELECT rowid, publisher, topic, payload, 'pending', datetime(created_at,'unixepoch'), ttl_seconds
                FROM events_v1_legacy""")
            w.conn.execute("DROP TABLE events_v1_legacy")
            w.conn.commit()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# MCP Protocol — stdio transport
# ---------------------------------------------------------------------------

def send_response(response: dict):
    """Send a JSON-RPC response over stdout."""
    print(json.dumps(response), flush=True)


def send_error(request_id, code: int, message: str, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    send_response({"jsonrpc": "2.0", "id": request_id, "error": err})


def send_result(request_id, result):
    send_response({"jsonrpc": "2.0", "id": request_id, "result": result})


# Tool definitions
TOOLS = [
    {
        "name": "publish_event",
        "description": "Publish an event to the inter-agent event bus. Other agents can subscribe to it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type": {
                    "type": "string",
                    "description": "Routing key, format category:name (e.g. 'feifei:gradient', 'agent:heartbeat')",
                },
                "payload": {
                    "type": "object",
                    "description": "JSON-serialisable data payload",
                },
                "source_agent": {
                    "type": "string",
                    "description": "Name of the publishing agent (e.g. 'feifei', 'xuefeng')",
                    "default": "unknown",
                },
                "ttl_seconds": {
                    "type": "integer",
                    "description": "Time-to-live in seconds (default 86400 = 24h)",
                    "default": 86400,
                },
            },
            "required": ["event_type", "payload"],
        },
    },
    {
        "name": "subscribe_events",
        "description": "Read new events matching a pattern. Cursor is auto-tracked per (consumer_id, pattern).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "event_type_pattern": {
                    "type": "string",
                    "description": "Wildcard pattern, e.g. 'feifei:*', 'agent:*', '*' for all",
                },
                "consumer_id": {
                    "type": "string",
                    "description": "Unique consumer name for cursor tracking (e.g. 'xuefeng')",
                },
                "max_events": {
                    "type": "integer",
                    "description": "Max events to return (1-100)",
                    "default": 10,
                },
            },
            "required": ["event_type_pattern", "consumer_id"],
        },
    },
    {
        "name": "event_bus_status",
        "description": "Show event bus status: event count, active cursors, topic histogram, health.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def handle_initialize(request_id, params):
    server_info = {
        "name": "hermes-event-bus",
        "version": "2.0.0",
        "description": "Inter-agent event bus for autonomous Hermes agents",
    }
    send_result(request_id, {
        "protocolVersion": params.get("protocolVersion", "2024-11-05"),
        "capabilities": {
            "tools": {},
            "prompts": {},
            "resources": {},
        },
        "serverInfo": server_info,
    })


def handle_list_tools(request_id):
    send_result(request_id, {"tools": TOOLS})


def handle_call_tool(request_id, params):
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    try:
        ensure_db()

        if tool_name == "publish_event":
            result = publish_event(
                event_type=arguments["event_type"],
                payload=arguments.get("payload", {}),
                source_agent=arguments.get("source_agent", "unknown"),
                ttl_seconds=arguments.get("ttl_seconds", 86400),
            )
            send_result(request_id, {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
            })

        elif tool_name == "subscribe_events":
            events = subscribe_events(
                event_type_pattern=arguments["event_type_pattern"],
                consumer_id=arguments["consumer_id"],
                max_events=arguments.get("max_events", 10),
            )
            if events:
                lines = [f"→ {len(events)} event(s):"]
                for e in events:
                    lines.append(f"  [{e['event_id']}] {e['event_type']} from {e['source_agent']}")
                text = "\n".join(lines)
            else:
                text = f"→ 0 new events for {arguments['consumer_id']}"
            send_result(request_id, {
                "content": [{"type": "text", "text": text}],
            })

        elif tool_name == "event_bus_status":
            status = event_bus_status()
            lines = [
                f"  Total events:  {status.get('total_events', '?')}",
                f"  Active cursors:{status.get('active_cursors', '?')}",
            ]
            topics = status.get("topic_histogram", {})
            if topics:
                lines.append("  Topics:")
                for t, c in sorted(topics.items(), key=lambda x: -x[1]):
                    lines.append(f"    {t}: {c}")
            send_result(request_id, {
                "content": [{"type": "text", "text": "\n".join(lines)}],
            })

        else:
            send_error(request_id, -32601, f"Unknown tool: {tool_name}")

    except Exception as e:
        tb = traceback.format_exc()
        send_error(request_id, -32000, str(e), tb)


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    """Read JSON-RPC 2.0 messages from stdin, dispatch, respond on stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            # Can't respond without an id — skip
            continue

        msg_id = msg.get("id")
        method = msg.get("method")
        params = msg.get("params", {})
        msgid = msg.get("id")

        if method == "initialize":
            handle_initialize(msgid, params)
        elif method == "tools/list":
            handle_list_tools(msgid)
        elif method == "tools/call":
            handle_call_tool(msgid, params)
        elif method == "notifications/initialized":
            # No response needed for this notification
            pass
        else:
            send_error(msgid, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    main()
