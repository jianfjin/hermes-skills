#!/usr/bin/env python3
"""Quick smoke test for publish_event.py — uses importlib for hyphens-in-path."""
import importlib.util
import os
import sqlite3

db_dir = os.path.expanduser("~/.hermes/hermes-agent/skills/autonomous-ai-agents/inter-agent-event-bus")
db_path = os.path.join(db_dir, "event_bus.db")
if os.path.exists(db_path):
    os.remove(db_path)

spec = importlib.util.spec_from_file_location(
    "publish_event",
    os.path.join(db_dir, "tools", "publish_event.py"),
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
publish_event = mod.publish_event

# Test 1: basic publish
r = publish_event(topic="agent:heartbeat", payload={"status": "ok"})
assert r["status"] == "published" and r["topic"] == "agent:heartbeat"
assert len(r["event_id"]) == 36 and isinstance(r["timestamp"], float)
print(f"TEST 1 OK: event_id={r['event_id']}")

# Test 2: custom TTL
r2 = publish_event(topic="skill:complete", payload={"result": 42}, ttl_seconds=3600)
assert r2["status"] == "published"
print(f"TEST 2 OK: ttl=3600")

# Test 3: default payload
r3 = publish_event(topic="agent:ping")
assert r3["status"] == "published"
print(f"TEST 3 OK: default payload")

# Test 4: invalid topic
try:
    publish_event(topic="Invalid_Topic")
    assert False
except ValueError:
    print("TEST 4 OK: invalid topic rejected")

# Test 5: non-serializable payload
try:
    publish_event(topic="agent:error", payload=complex(1, 2))
    assert False
except TypeError:
    print("TEST 5 OK: non-serializable payload rejected")

# Test 6: hyphens and underscores in topic
r6 = publish_event(topic="my-agent:data_pipeline-v2")
assert r6["status"] == "published"
print(f"TEST 6 OK: hyphens/underscores topic")

# Test 7: verify persisted in DB
conn = sqlite3.connect(db_path)
row = conn.execute(
    "SELECT event_id, topic, payload FROM events WHERE event_id = ?",
    (r["event_id"],),
).fetchone()
assert row is not None and row[1] == "agent:heartbeat"
conn.close()
print("TEST 7 OK: event persisted in DB")

os.remove(db_path)
print("\nAll 7 tests passed!")
