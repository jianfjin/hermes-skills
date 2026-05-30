# Multi-Round Debate Cadence (2026-05-17)

Pattern established during SCAILED WP4 project where 3 sequential debates were needed:
Round 1: Frontend selection (5 seats)
Round 2: Database selection (5 seats)  
Round 3: Agent-D comparison (8 seats)

## Pattern

1. **Write all briefs upfront in one `execute_code` call**. Use Python's `read_file` + `write_file` (hermes_tools) to read shared briefs and write per-agent prompt files. This is faster than multiple `write_file` tool calls.

2. **Launch Round 1 agents**: kimi-k2.6 profiles FIRST (Musk, Guido, Dijkstra, Jobs), deepseek profiles SECOND (Linus, Xiaolong, Xuefeng, Jensen). All with `background=True, notify_on_complete=True`.

3. **Present Round 1 synthesis while Round 2 launches**. Don't make the user wait for all rounds — show intermediate results.

4. **Reuse the same brief file pattern**: `/tmp/audit_<topic>_<role>.txt` naming convention.

5. **Log all outputs** with `process(action='log', session_id=..., limit=200)` for archiving.

## Example code

```python
from hermes_tools import read_file, write_file

brief = read_file("/tmp/shared_brief.txt")["content"]

questions = {
    "musk": "Role: CVO...\nQuestion: ...",
    "linus": "Role: Chief Architect...\nQuestion: ...",
}

for role, question in questions.items():
    prompt = brief + "\n\n---\n\n" + question
    write_file(f"/tmp/audit_topic_{role}.txt", prompt)
```

Then launch:
```python
terminal(command="musk chat -q \"$(cat /tmp/audit_topic_musk.txt)\"",
         background=True, notify_on_complete=True, timeout=600)
```

## Pitfall: `terminal()` curl vs urllib

When communicating results back via webhook after debates, `terminal()` tool's `curl` produces empty output for webhook POSTs. Use `execute_code` with `urllib.request` instead.
