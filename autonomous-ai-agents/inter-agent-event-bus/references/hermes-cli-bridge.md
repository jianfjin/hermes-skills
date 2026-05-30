# Hermes CLI Bridge: How spawn_profile_agent Works

## The Problem

The daemon needs to invoke a profile agent (e.g., `feifei`) without being inside that profile's session. The daemon runs as a subprocess under systemd — it has no direct access to Hermes agent runtime internals.

## The Solution: subprocess + Environment Variables

```python
def spawn_profile_agent(self, profile, event_id, topic, payload):
    hermes_bin = self._resolve_hermes_path()
    goal = f"handle {topic} event {event_id}"

    env = os.environ.copy()
    env["HERMES_EVENT_ID"] = event_id
    env["HERMES_TOPIC"] = topic
    env["HERMES_PAYLOAD"] = json.dumps(payload)
    env["HERMES_PROFILE"] = profile

    cmd = [hermes_bin, "profile", profile, "chat", "-q", f"Process event: {goal}"]
    
    try:
        result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
        return make_success(event_id=event_id, summary=result.stdout[:500])
    except subprocess.TimeoutExpired:
        return make_timeout(event_id=event_id)
    except Exception as e:
        return make_failure(event_id=event_id, errors=[str(e)])
```

## Hermes Path Resolution

The daemon tries two strategies in order:

```python
def _resolve_hermes_path(self):
    # Strategy 1: known installation path
    known = os.path.expanduser("~/.hermes/hermes-agent/hermes")
    if os.path.exists(known):
        return known
    # Strategy 2: system PATH
    return "hermes"
```

Strategy 2 is preferred for portability, but strategy 1 is needed when PATH doesn't include the Hermes installation (e.g., systemd services with restricted PATH).

## Environment Variables vs CLI Arguments

Environment variables are preferred over CLI arguments for passing event context:

- **Environment variables:** invisible to `ps`, surfacing only via `/proc/<pid>/environ` (requires same user or root)
- **CLI arguments:** visible to any process that runs `ps aux` (security concern if payload contains sensitive data)
- **Temporary files:** most secure option (file permission 600), not yet implemented

## Returning Structured Results

The daemon uses `SubagentResult` TypedDict (from `daemon_2b_schema.py`):

```python
class SubagentResult(TypedDict, total=False):
    event_id: str
    status: Literal["completed", "failed", "timeout", "partial"]
    processed_at: float
    errors: List[str]
    summary: str
    side_effects: List[str]
```

## Failure Modes

| Mode | Scenario | Status Code | Recovery |
|------|----------|-------------|----------|
| Non-zero exit | hermes CLI exits with error | "failed" | Record failure → retry → DLQ |
| TimeoutExpired | hermes doesn't respond in 30s | "timeout" | Record failure → retry → DLQ |
| FileNotFoundError | hermes binary not found | "failed" | Log WARN → skip (can't retry) |
| OOM | subprocess killed by kernel | No output → silent | DLQ background check |
| Crash mid-response | subprocess dumps core | Partial stdout | DLQ background check |

## Security Considerations

- `HERMES_PAYLOAD` contains raw JSON — visible via `/proc/<pid>/environ` under same user
- The profile name from YAML route config is NOT user-controlled (admin only)
- `goal` string truncation (200 chars max) prevents CLI argument overflow
- No shell injection via subprocess list mode (not shell=True)
