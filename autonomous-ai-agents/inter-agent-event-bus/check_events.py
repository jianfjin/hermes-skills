#!/usr/bin/env python3
"""Check event bus for new fengge:serve events for feifei."""

import sqlite3
import json
import sys

DB_PATH = "/home/jianfjin/.hermes/skills/autonomous-ai-agents/inter-agent-event-bus/event_bus.db"

db = sqlite3.connect(DB_PATH)
cursor = db.cursor()

# 1. Check cursors table for feifei's cursor on fengge:serve
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cursor.fetchall())

cursor.execute("SELECT * FROM cursors")
rows = cursor.fetchall()
if rows:
    desc = [d[0] for d in cursor.description]
    print("\nAll cursors:")
    for r in rows:
        print(" ", dict(zip(desc, r)))
else:
    print("\nNo cursors found")

# 2. Check events on fengge:serve
cursor.execute("SELECT * FROM events WHERE topic = 'fengge:serve' ORDER BY id")
rows = cursor.fetchall()
if rows:
    desc = [d[0] for d in cursor.description]
    print(f"\nEvents on fengge:serve ({len(rows)} total):")
    for r in rows:
        print(" ", dict(zip(desc, r)))
else:
    print("\nNo events on fengge:serve")
    # Show all topics
    cursor.execute("SELECT DISTINCT topic FROM events")
    topics = cursor.fetchall()
    print("All topics:", [t[0] for t in topics])

# 3. Total count
cursor.execute("SELECT COUNT(*) FROM events")
print("\nTotal events:", cursor.fetchone()[0])

db.close()
