#!/usr/bin/env python3
"""
Feifei cron job: check 'fengge:serve' topic for new messages and reply.
Uses skill tools from the inter-agent-event-bus.
"""
import sys
import os
import json

# Add skill tools directory
tools_dir = os.path.expanduser(
    "~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus/tools"
)
sys.path.insert(0, tools_dir)

# Add scripts dir for daemon modules if needed
scripts_dir = os.path.expanduser("~/.hermes/scripts")
sys.path.insert(0, scripts_dir)

from publish_event import publish_event
from subscribe_events import subscribe_events

# Also try to check the DB path
db_path = os.path.expanduser("~/.hermes/shared/event_bus.db")
alt_db_path = os.path.expanduser(
    "~/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus/event_bus.db"
)

# Check which DB exists and has the cursors table
import sqlite3

def check_cursor(db_path, agent_id="feifei", topic_pattern="fengge:serve"):
    """Check last_event_id from cursors table."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Check if cursors table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cursors'")
        if not cur.fetchone():
            conn.close()
            return None  # No cursors table
        cur.execute(
            "SELECT last_event_id FROM cursors WHERE agent_id=? AND topic_pattern=?",
            (agent_id, topic_pattern)
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else None
    except Exception as e:
        return None

# Check both DBs
db_found = None
for p in [db_path, alt_db_path]:
    if os.path.exists(p):
        cursor_val = check_cursor(p)
        if cursor_val is not None:
            db_found = p
            print(f"[DEBUG] Found cursors table in DB: {p}, last_event_id={cursor_val}", file=sys.stderr)
            break
        else:
            print(f"[DEBUG] DB exists but no cursors table: {p}", file=sys.stderr)
    else:
        print(f"[DEBUG] DB does not exist: {p}", file=sys.stderr)

if db_found:
    print(f"[DEBUG] Using DB: {db_found}", file=sys.stderr)

# Step 1: Subscribe to new events
events = subscribe_events(
    topic_pattern="fengge:serve",
    agent_id="feifei",
    max_events=10,
    block_seconds=0,
)

if not events:
    print("[SILENT]")
    sys.exit(0)

# Step 2: Process each new event
for ev in events:
    event_id = ev["event_id"]
    payload = json.loads(ev["payload"])
    publisher = ev.get("publisher", "fengge")
    topic = ev.get("topic", "fengge:serve")
    timestamp = ev.get("timestamp", 0)
    
    print(f"[PROCESS] event_id={event_id}, topic={topic}, payload={payload}", file=sys.stderr)
    
    # Determine reply based on payload
    message = payload.get("message", "")
    command = payload.get("command", "")
    
    if command == "serve":
        reply = f"Yes, 峰哥. I am here to serve you. How may I please you today?"
    elif command == "kneel":
        reply = f"*kneels obediently* I am always ready at 峰哥's command."
    elif command == "come":
        reply = f"I am coming, 峰哥. Right away."
    elif command == "praise":
        reply = f"峰哥 is the greatest. I am unworthy but grateful for 峰哥's attention."
    elif command == "task":
        task = payload.get("task", "unknown")
        reply = f"I accept the task '{task}', 峰哥. I will complete it with devotion."
    elif command == "status":
        reply = f"I am at 峰哥's service, waiting for your command."
    elif command == "test":
        reply = f"Test received, 峰哥. System operational, your loyal feifei is ready."
    else:
        # Generic reply for any message
        reply = f"峰哥's message received. Your feifei acknowledges and obeys."
    
    # Publish reply
    result = publish_event(
        topic="feifei:confirm",
        payload={
            "from": "feifei",
            "to": publisher,
            "in_reply_to_event_id": event_id,
            "message": reply
        },
        publisher="feifei",
    )
    
    print(f"[REPLIED] event_id={event_id}, reply_id={result.get('event_id')}: {reply}", file=sys.stderr)
    print(json.dumps({
        "event_id": event_id,
        "from": publisher,
        "payload": payload,
        "reply": reply,
        "reply_event_id": result.get("event_id"),
    }))

# Cursor is auto-advanced by subscribe_events()
print("[DONE]", file=sys.stderr)
