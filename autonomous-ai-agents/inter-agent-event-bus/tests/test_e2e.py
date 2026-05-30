#!/usr/bin/env python3
"""End-to-end test for inter-agent event bus skill."""
import json, os, sys, time

# Add skill to path
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(SKILL_DIR, "tools"))
sys.path.insert(0, os.path.join(SKILL_DIR, "hooks"))

# Set DB to temp file
os.environ["EVENT_BUS_DB_PATH"] = "/tmp/test_event_bus_e2e.db"

# Clean previous test DB
for f in ["/tmp/test_event_bus_e2e.db", "/tmp/test_event_bus_e2e.db-wal", "/tmp/test_event_bus_e2e.db-shm"]:
    try: os.remove(f)
    except: pass

from publish_event import publish_event
from subscribe_events import subscribe_events
from event_bus_status import event_bus_status

passed = 0
failed = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} — {detail}")

# === 1. Basic publish → subscribe ===
r = publish_event(topic="feifei:gradient", payload={"loss": 0.023}, publisher="feifei")
check("publish returns event_id", "event_id" in r)
eid = r["event_id"]

events = subscribe_events(topic_pattern="feifei:*", agent_id="test_agent")
check("subscribe gets 1 event", len(events) == 1, f"got {len(events)}")
check("event contains expected fields", all(k in events[0] for k in ["event_id", "topic", "payload", "publisher"]))
check("publisher is feifei", events[0]["publisher"] == "feifei")
check("topic correct", events[0]["topic"] == "feifei:gradient")

# === 2. Cursor advancement — second poll returns nothing ===
events2 = subscribe_events(topic_pattern="feifei:*", agent_id="test_agent")
check("cursor advances — second poll empty", len(events2) == 0, f"got {len(events2)}")

# === 3. Multi-topic cursors ===
publish_event(topic="system:heartbeat", payload={"tick": 1}, publisher="system")
publish_event(topic="feifei:loss", payload={"v": 0.01}, publisher="feifei")

e_feifei = subscribe_events(topic_pattern="feifei:*", agent_id="test_agent")
e_system = subscribe_events(topic_pattern="system:*", agent_id="test_agent")
check("feifei cursor independent", len(e_feifei) == 1, f"got {len(e_feifei)}")
check("system cursor independent", len(e_system) == 1, f"got {len(e_system)}")

# === 4. Invalid topic rejection ===
try:
    publish_event(topic="invalid", payload={}, publisher="test")
    check("rejects invalid topic", False, "should have raised")
except ValueError:
    check("rejects invalid topic", True)

# === 5. Status tool ===
st = event_bus_status()
check("status has total_events", st.get("total_events", -1) >= 4, f"got {st}")
check("status has active_cursors", st.get("active_cursors", -1) >= 1)
check("status has topic_histogram", len(st.get("topic_histogram", {})) >= 2)

# === 6. Multiple subscribers ===
publish_event(topic="broadcast:all", payload={"msg": "hello"}, publisher="system")
a1 = subscribe_events(topic_pattern="broadcast:*", agent_id="agent_a")
a2 = subscribe_events(topic_pattern="broadcast:*", agent_id="agent_b")
check("two subscribers both receive", len(a1) == 1 and len(a2) == 1)

# === 7. Empty results ===
e_empty = subscribe_events(topic_pattern="nonexistent:*", agent_id="test_agent")
check("empty pattern returns []", len(e_empty) == 0)

# === Summary ===
print(f"\n{'='*40}")
print(f"Results: {passed}/{passed+failed} passed, {failed} failed")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"{failed} test(s) FAILED")
    sys.exit(1)
