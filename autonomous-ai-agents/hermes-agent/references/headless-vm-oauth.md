# Headless VM OAuth Device-Code Flow

## Problem

VM has no browser. `hermes model` requires an interactive TTY. OAuth providers
(OpenAI Codex, GitHub Copilot) redirect to a local web server that doesn't
exist on the VM.

## Solution: CLI Device-Code Auth

```bash
# All providers that support OAuth:
hermes auth add openai-codex --no-browser --timeout 600
hermes auth add github-copilot --no-browser --timeout 600
```

This prints a URL and device code to stdout. Open the URL on a device
with a browser (phone, laptop), enter the code, and authorize.

## Pitfalls

### 1. Terminal tool output buffering

When run via `terminal()` (Hermes tool), stdout may not flush immediately.
The auth command appears to hang with no output.

**Fix:** Use `pty=true` + `process(action="wait")` with a short initial wait,
or run in background with PTY enabled:

```python
terminal(
    command="hermes auth add openai-codex --no-browser --timeout 600",
    background=True,
    pty=True,
    timeout=10,
)
# Wait a few seconds for the device code to be printed
process(session_id="proc_xxx", action="wait", timeout=10)
process(session_id="proc_xxx", action="log")  # Read the URL + code
```

### 2. Extended wait for user interaction

After printing the code, the command blocks indefinitely waiting for the
user to complete the browser flow. The `--timeout` argument (default: 300s)
is the safety valve. Set it high enough for the user to walk to another
device.

### 3. Not all auth providers support --no-browser

- `openai-codex` ✅
- `github-copilot` ✅
- `anthropic` — uses API key, not OAuth
- `nous` / `qwen-oauth` — depends on OAuth portal config

Run `hermes auth add <provider> --help` to check.

### 4. Profile OAuth

Credential pools are global, not per-profile. Once `hermes auth add` stores
the credential, any profile can use it by configuring:

```yaml
# ~/.hermes/profiles/<name>/config.yaml
model:
  provider: openai-codex
  default: gpt-4o
```

No per-profile re-auth needed.
