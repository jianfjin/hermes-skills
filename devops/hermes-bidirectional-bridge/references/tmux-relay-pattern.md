# Tmux Relay Pattern — WhatsApp Agent Bridging to Local CLI

Last verified: 2026-05-22

## Problem

A local Hermes CLI agent (running in tmux `work:2`) lacks the WhatsApp messaging platform configured (`platforms.whatsapp` missing, messaging toolset absent). `send_message(target="whatsapp")` fails even when `WHATSAPP_HOME_CHANNEL` is set — the tool needs the platform configured at the gateway level.

The user wants to communicate with this local agent from WhatsApp without configuring another WhatsApp gateway instance.

## Solution: Relay Pattern

The WhatsApp-capable agent acts as a bridge — it receives user messages on WhatsApp and forwards them to the local CLI agent via tmux injection, then captures the response and relays it back.

```
User ←WhatsApp→ Bridge Agent ←tmux injection→ Local Agent (work:2)
                      (this agent)        capture-pane
```

## Steps

### 1. Verify the target window runs Hermes (not bash)

```bash
# Before injecting, check the window state
tmux capture-pane -t work:2 -p | tail -5
# Look for the Hermes prompt: ❯ or ⚕
# If it shows "bash" or "$", Hermes exited — restart it
```

### 2. Restart Hermes if needed

```bash
tmux send-keys -t work:2 "hermes" Enter
# Wait 5-8s for banner + model load
sleep 6
```

### 3. Inject message

```bash
tmux send-keys -t work:2 "<message>" Enter
```

### 4. Wait for processing, capture response

```bash
sleep 6 && tmux capture-pane -t work:2 -p | tail -15
# Longer commands may need 15-30s
# Complex tasks with tool calls may need 30-60s
```

### 5. Relay captured output to user

Strip captured pane artifacts (timestamps, status bars) and present the agent's response.

## Full Worked Example (2026-05-22)

```bash
# Step 1: Verify window state
tmux list-windows -t work
# → 2: bash* (Hermes exited!) 

# Step 2: Relaunch Hermes
tmux send-keys -t work:2 "hermes" Enter
sleep 6

# Step 3: Verify it's running
tmux capture-pane -t work:2 -p | tail -5
# → ❯  (Hermes prompt)

# Step 4: Inject message
tmux send-keys -t work:2 "本地峰哥，当前项目状态？" Enter

# Step 5: Wait and capture
sleep 8 && tmux capture-pane -t work:2 -p | tail -15
```

## Pitfalls

### Hermes exits after Ctrl+C or `/reset`

Symptom: `tmux send-keys` text appears in bash prompt with "command not found" error.

Root cause: Interrupting Hermes (Ctrl+C) or `/reset` during certain phases causes the CLI process to exit entirely. The tmux window falls back to the parent bash shell. Subsequent `send-keys` go to bash, not Hermes.

Prevention: Always `capture-pane` to verify Hermes is alive before injecting. Look for `❯` (Hermes prompt) vs `$ ` (bash prompt).

Recovery: `tmux send-keys -t work:2 "hermes" Enter` and wait 6s.

### send_message fails even with WHATSAPP_HOME_CHANNEL set

If the WhatsApp platform isn't configured in `config.yaml` under `platforms:`, `send_message(target="whatsapp")` returns `[error]` regardless of `WHATSAPP_HOME_CHANNEL`. The tool requires the gateway platform to be initialized. This is NOT fixed by `hermes config set WHATSAPP_HOME_CHANNEL` alone.

Fix: Either configure WhatsApp as a gateway platform (may conflict with existing WhatsApp gateway on another machine) or use the tmux relay pattern documented here.

### Double-injection concatenation

If two `tmux send-keys` calls fire in rapid succession (no `sleep` between), the second keys may be injected before the first Enter is processed, concatenating both into one line. This caused `/reset` + test message to become `/reset测试消息` → "Unknown command".

Fix: Always `sleep 1-2` between consecutive send-keys, or batch related commands into one send-keys call with `&&`.
