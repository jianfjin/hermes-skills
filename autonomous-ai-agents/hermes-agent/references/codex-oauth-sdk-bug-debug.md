# OpenAI Codex OAuth: SDK `NoneType` Bug — Full Diagnostic

**Date discovered:** 2026-05-30
**Affected:** OpenAI Python SDK v2.32.0–v2.38.0
**Affected providers:** `openai-codex` (OAuth device-code flow)
**All models affected:** gpt-5.5, gpt-5.3-codex, gpt-5.2-codex, etc.

## Symptoms

When using `hermes chat -q '...' --model gpt-5.3-codex --provider openai-codex`, the agent immediately crashes with:

```
Error: 'NoneType' object is not iterable
```

In `~/.hermes/logs/agent.log`:
```
WARNING API call failed (attempt 1/3) error_type=TypeError
provider=openai-codex base_url=https://chatgpt.com/backend-api/codex
model=gpt-5.3-codex summary='NoneType' object is not iterable
ERROR Non-retryable client error: 'NoneType' object is not iterable
```

**KEY DIFFERENTIATOR:** The error fires on attempt **1/3** and is labeled `Non-retryable client error`. This means it's NOT a transient network issue or model entitlement — it's a response parsing crash.

## Root Cause

The OpenAI Python SDK's `parse_response()` function in `openai/lib/_parsing/_responses.py` (line 61) iterates over `response.output` without guarding against `None`:

```python
# Bug in SDK v2.32.0–v2.38.0, line 61
for output in response.output:
```

The Codex OAuth backend (`chatgpt.com/backend-api/codex`) sends stream events where the response object has `"output": null`. This is valid JSON — the Codex backend delivers content entirely via stream event deltas (`response.output_text.delta`), and the final `response.completed` event has `output: null` or `output: []`.

The SDK's `responses.stream()` context manager calls `parse_response()` when processing the `response.completed` event, and crashes.

## Diagnostic Steps

### 1. Verify OAuth credential exists

```bash
hermes auth list openai-codex
# Should show: openai-codex (1 credentials):
#   #1  openai-codex-oauth-1 oauth   device_code ←
```

The credential is stored in `~/.hermes/auth.json` under `credential_pool.openai-codex`.

### 2. Test the Codex models endpoint directly

```python
import httpx, json
d = json.load(open('/home/jianfjin/.hermes/auth.json'))
token = d['credential_pool']['openai-codex'][0]['access_token']
resp = httpx.get(
    'https://chatgpt.com/backend-api/codex/models?client_version=1.0.0',
    headers={'Authorization': f'Bearer {token}'},
    timeout=15,
)
print(resp.json().get('models', []))
```

### 3. Reproduce with OpenAI SDK directly

```python
from openai import OpenAI
client = OpenAI(base_url='https://chatgpt.com/backend-api/codex', api_key=token)

# This WILL crash with NoneType
try:
    with client.responses.stream(
        model='gpt-5.3-codex',
        input=[{'role': 'user', 'content': 'hi'}],
        instructions='helpful',
        store=False,
    ) as stream:
        for event in stream:
            pass
except TypeError as e:
    print(f'SDK bug confirmed: {e}')
```

### 4. Confirm the SDK bug location

```bash
grep -n 'for output in response.output' \
  ~/.local/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py
# → line 61
```

## Fix

Patch line 61 from:
```python
for output in response.output:
```
to:
```python
for output in (response.output or []):
```

**Two locations must be patched:**

| Location | Used by |
|----------|---------|
| `~/.local/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py` | Standalone Python (`python3 -c ...`, `execute_code`) |
| `~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py` | Hermes agent CLI (`hermes chat`, etc.) |

## Verification

After patching, test:
```bash
hermes -p <profile> chat -q 'Hi' --model gpt-5.3-codex --provider openai-codex
# Expected: model responds normally (no error)
```

## Maintenance

The patch is overwritten by `pip install --upgrade openai`. After any SDK upgrade, re-apply:

```bash
for f in \
  ~/.local/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py \
  ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/openai/lib/_parsing/_responses.py; do
  [ -f "$f" ] && sed -i 's/for output in response\.output:/for output in (response.output or []):/' "$f"
done
```

## Codex OAuth Quirks

| Quirk | Detail |
|-------|--------|
| streaming required | `stream=True` — non-streaming returns 400 |
| input format | Must be a list: `[{"role": "user", "content": "..."}]` |
| model entitlements | Not all `DEFAULT_CODEX_MODELS` in `codex_models.py` are available |
| context window | Codex models: 272K tokens max (except spark: 128K) |
| SDK versions affected | 2.32.0 through 2.38.0+ (bug persists in latest as of May 2026) |
