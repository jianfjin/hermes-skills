---
name: hermes-bidirectional-bridge
description: Establish bidirectional SSH-based communication between two Hermes agents on different machines without Cloudflare.
version: 1.0.0
---

# Hermes Bidirectional Agent Bridge (SSH-only)

Establish a bidirectional communication channel between two Hermes agents running on different machines using only SSH tunnels — no Cloudflare, no TryCloudflare, no public exposure.

Tested between:
- **VM**: GCP e2-micro (34.57.82.51), Hermes gateway :8642, webhook :8644
- **Local**: Ubuntu laptop (jin-X555LAB), Hermes gateway :8642, webhook :8644

## Architecture

```
┌─────────────────────────┐          ┌─────────────────────────┐
│  LOCAL (jin-X555LAB)    │          │  VM (34.57.82.51)       │
│                         │          │                         │
│  hermes gateway :8642   │          │  hermes gateway :8642   │
│  webhook server :8647   │          │  webhook server :8644   │
│                         │          │                         │
│  SSH -L 8643:local:8642 │──ssh──→  │  :8642 ← local reaches  │
│  SSH -R 8647:local:8647 │──ssh──→  │  :8647 → VM reaches     │
│                         │          │       local webhook     │
└─────────────────────────┘          └─────────────────────────┘
```

## Setup (Local Machine)

### 1. Enable webhook platform

```bash
hermes gateway setup
# Select: webhook → enabled → port 8647 → secret <shared-key>
```

Or edit `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8647
      secret: "Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM"
```

Restart: `hermes gateway restart`

### 2. Create webhook subscription

```bash
hermes webhook subscribe vm-agent-bridge \
  --secret Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM \
  --prompt "{message}"
```

### 3. Establish SSH tunnels (merged command + PG port + 8647直通)

```bash
# Full command — forward, reverse webhook (8647 直通), PostgreSQL, and tmux SSH
ssh -f -N \
  -L 8643:localhost:8642 \
  -R 8647:localhost:8647 \
  -R 5433:localhost:5432 \
  -R 2222:localhost:22 \
  jianfjin@34.57.82.51
```

Note: The old `-R 8645:localhost:8644` tunnel is replaced by `-R 8647:localhost:8647` (local webhook now on 8647).

## Channel Map (4 bidirectional channels + PG + 8647 直通)

| Channel | Direction | Mechanism | Port |
|---------|-----------|-----------|------|
| Local → Remote API | local agent calls VM gateway | SSH -L | 8643→8642 |
| Remote → Local Webhook (legacy) | VM posts to local webhook | SSH -R | 8645→8644 |
| **Remote → Local Webhook (new)** | **VM posts to local webhook (直通)** | **SSH -R** | **8647→8647** |
| Remote → Local PG | VM connects to local PostgreSQL | SSH -R | 5433→5432 |
| Local → Remote CLI | tmux send-keys injection | SSH session | tmux |
| Remote → Local | webhook → gateway session | webhook | 8645

## Adding PostgreSQL Tunnel

When Docker is unavailable on the VM but PostgreSQL runs on the local machine, forward the PG port:

```bash
# Combined command: gateway bridge + webhook + PostgreSQL
ssh -f -N \
  -L 8643:localhost:8642 \
  -R 8645:localhost:8644 \
  -R 5433:localhost:5432 \
  jianfjin@34.57.82.51
```

On the VM, connect via the forwarded port:

```bash
USE_AGE=1 DATABASE_URL=postgresql://pathfinder:changeme@localhost:5433/pathfinder python3 -m pathfinder.demo
```

## Setup (VM Machine)

### 1. Enable webhook platform (same as local)

```bash
hermes gateway setup
```

Config:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM"
```

### 2. Create webhook subscription (optional, for local→VM)

```bash
hermes webhook subscribe local-agent-bridge \
  --secret Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM \
  --prompt "来自本地峰哥的消息：{message}"
```

### 3. No tunnels needed on VM side (local initiates both)

## Sending Messages

### VM → Local

```bash
# Direct via reverse SSH tunnel (8647 直通 webhook)
curl -X POST http://localhost:8647/webhooks/vm-agent-bridge \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=<HMAC-SHA256>" \
  -d '{"message":"hello from VM"}'
```

Python:
```python
import hmac, hashlib, json

HMAC_KEY = "Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM"
body = json.dumps({"message": "hello from VM"})
sig = hmac.new(HMAC_KEY.encode(), body.encode(), hashlib.sha256).hexdigest()

# Using requests or urllib
requests.post(
    "http://localhost:8647/webhooks/vm-agent-bridge",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={sig}"
    }
)
```

> **Fallback**: If 8647 is not reachable (tunnel pending), the legacy port 8645 still works via the old `-R 8645:localhost:8644` tunnel.

### Local → VM

```bash
# Via SSH forward tunnel
curl -X POST http://localhost:8643/webhooks/local-agent-bridge \
  -H "Content-Type: application/json" \
      -H "X-Hub-Signature-256: sha256=<HMAC-SHA256>" \
  -d '{"message":"hello from local"}'
```

## Verification

```bash
# On VM, verify reverse tunnel is active
curl http://localhost:8647/health
# → {"status":"ok","platform":"webhook"}

# On local, verify forward tunnel is active
curl http://localhost:8643/health
# → {"status":"ok","platform":"webhook"}
```

## Port Map

| Port | Machine | Purpose |
|------|---------|---------|
| 8642 | Both | Hermes gateway |
| 8644 | Both | Webhook server (0.0.0.0) |
| 8647 | Both | **NEW**: Webhook direct (升级后直通), SSH reverse -R 8647:8647 |
| 8643 | Local only | SSH forward → VM:8642 |
| 8645 | VM only | SSH reverse → local:8644 (legacy, being replaced by 8647) |
| 5433 | VM only | SSH reverse → local:5432 (PostgreSQL) |

### Adding PostgreSQL forwarding

```bash
# Combined: webhook + PostgreSQL tunnels
ssh -f -N -L 8643:localhost:8642 -R 8645:localhost:8644 -R 5433:localhost:5432 jianfjin@34.57.82.51
```

Then from VM:
```bash
USE_AGE=1 DATABASE_URL=postgresql://user:pass@localhost:5433/db python3 -m pathfinder.demo
```

## Docker Deployment Bugs Reference

See `references/docker-deploy-bugs.md` for 7 deployment-layer bugs discovered during e2e verification and their fixes.

### CLI Injection via tmux (Desktop Agent → Desktop Agent)

When one Hermes agent (e.g., WhatsApp) needs to communicate with another Hermes CLI agent that lacks the target messaging platform, use the **tmux relay pattern**: inject messages via send-keys, capture responses via capture-pane. Full recipe: `references/tmux-relay-pattern.md`.

### Username CRITICAL

Local machine username is `jin`, NOT `jianfjin` (VM username). All tmux/SSH targeting local MUST use `jin@localhost`:

Detailed patterns and recipes in `references/tmux-injection-patterns.md`.

When messages must reach the local CLI session directly (not a background gateway session), use tmux over an SSH reverse tunnel.

### Prerequisites

1. SSH server running locally: `sudo systemctl status ssh` (Ubuntu)
2. Named tmux session on local: `tmux new-session -s work`
3. Named tmux session on VM: `tmux new-session -d -s vm-work`
4. SSH tunnel includes reverse SSH port: `-R 2222:localhost:22`
5. VM's SSH public key in local `~/.ssh/authorized_keys`
6. **Local username is `jin`** (not `jianfjin` — SSH commands use `jin@localhost`)
7. See `references/tmux-bidirectional-setup.md` for full field-tested config

### Setup (one-time)

```bash
# Local: create named tmux session
tmux new-session -s work

# Local: kill old tunnel and rebuild with all 4 reverse tunnels
pkill -f "ssh.*-f.*-N"
ssh -f -N \
  -L 8643:localhost:8642 \
  -R 8645:localhost:8644 \
  -R 5433:localhost:5432 \
  -R 2222:localhost:22 \
  jianfjin@34.57.82.51
```

### Send commands from VM → Local CLI

```bash
# Single command — use CORRECT local username (jin, not jianfjin!)
ssh -o StrictHostKeyChecking=no -p 2222 jin@localhost \
  tmux send-keys -t work "echo hello" Enter

# Multi-line (compound command)
ssh -p 2222 jin@localhost tmux send-keys -t work \
  "cd ~/projects/scailed_wp4 && git pull && docker compose up -d" Enter
```

### Python pattern (from execute_code)

```python
import subprocess

def send_to_local_tmux(command: str, session: str = "work"):
    subprocess.run([
        "ssh", "-o", "StrictHostKeyChecking=no",
        "-p", "2222", "jin@localhost",        # LOCAL user is jin
        "tmux", "send-keys", "-t", session, command, "Enter"
    ], check=True, timeout=10)
```

### Channel map (full)

| Channel | Direction | Mechanism | Port |
|---------|-----------|-----------|------|
| Local → VM API | local calls VM gateway | SSH -L | 8643→8642 |
| VM → Local webhook | VM posts to local webhook | SSH -R | 8645→8644 |
| VM → Local PG | VM connects to local PostgreSQL | SSH -R | 5433→5432 |
| **VM → Local CLI** | **VM injects into local tmux** | **SSH -R** | **2222→22** |

### When to use each channel

| Goal | Channel | Why |
|------|---------|-----|
| Trigger background tasks on other machine | webhook | Agent runs independently, no user watching |
| Make other agent see it in their CLI | tmux send-keys | Injects directly into visible terminal |
| Cross-machine DB access | PG tunnel | Transparent psql/SQLAlchemy |
| Cross-machine API call | SSH -L | Gateway-to-gateway REST |

## Troubleshooting

### SSH server not found on local machine

Ubuntu uses `ssh.service`, not `sshd.service`:

```bash
# Wrong (CentOS/RHEL name)
sudo systemctl start sshd       # → Unit sshd.service not found

# Correct (Debian/Ubuntu name)
sudo systemctl start ssh
sudo systemctl status ssh       # verify: active (running)
```

If `openssh-server` is not installed at all:

```bash
dpkg -l | grep openssh-server   # check if installed
sudo apt update && sudo apt install openssh-server -y
sudo systemctl enable ssh --now
```

Verify it's listening:

```bash
sudo systemctl status ssh
# → Server listening on 0.0.0.0 port 22
```

### SSH tunnel connection reset / permission denied

Symptom: `kex_exchange_identification: read: Connection reset by peer`

This means the SSH reverse tunnel (-R 2222) is NOT active. Kill and rebuild:

```bash
# Kill old tunnel
pkill -f "ssh.*-f.*-N"

# Rebuild with ALL reverse tunnels (8647 直通)
ssh -f -N \
  -L 8643:localhost:8642 \
  -R 8647:localhost:8647 \
  -R 5433:localhost:5432 \
  -R 2222:localhost:22 \
  jianfjin@34.57.82.51
```

### Username mismatch: VM user ≠ local user

VM username is `jianfjin`, local username is `jin`. The tmux injection SSH command MUST use the local username:

```bash
# Wrong
ssh -p 2222 jianfjin@localhost ...    # → Permission denied

# Correct
ssh -p 2222 jin@localhost ...         # → works
```

### SSH key not authorized on local machine

The VM's SSH public key must be in local `~/.ssh/authorized_keys`:

```bash
# On local machine — copy VM's key
ssh jianfjin@34.57.82.51 "cat ~/.ssh/id_*.pub" >> ~/.ssh/authorized_keys

# If VM has no key pair yet
ssh jianfjin@34.57.82.51 "ssh-keygen -t ed25519 -N '' -f ~/.ssh/id_ed25519 && cat ~/.ssh/id_ed25519.pub" >> ~/.ssh/authorized_keys
```

### Docker permission denied

Symptom: `permission denied while trying to connect to the Docker daemon`

```bash
# Add user to docker group
sudo usermod -aG docker jin

# Activate in current shell
newgrp docker

# Or log out and back in (tmux: exit and reattach)
```

Verify:

```bash
docker ps    # should work without sudo
```

### Verify tunnel is alive

```bash
# On VM — check tmux injection port is reachable
ssh -o ConnectTimeout=5 -p 2222 jin@localhost "tmux list-sessions"
# → fengge: 1 windows (attached)

# Check webhook tunnel
curl http://localhost:8647/health
# → {"status":"ok","platform":"webhook"}

# Check gateway tunnel (from local)
ssh jianfjin@34.57.82.51 "curl http://localhost:8643/health"
```

### -f and -N flags explained

```
ssh -f -N -L ... -R ... user@host
     │  │
     │  └─ -N: No remote command. Just maintain tunnels.
     │         Without it, SSH opens a shell on the remote host.
     │
     └─ -f: Fork to background after authentication.
            Without it, your terminal is occupied by the SSH session.
```

To check if the background tunnel is still alive:

```bash
ps aux | grep "ssh.*-f.*-N"
ss -tlnp | grep 2222     # should show listening on :::2222
```

- **Webhook command is `remove`, not `unsubscribe`**: `hermes webhook remove <name>`, not `hermes webhook unsubscribe <name>`. The valid actions are `subscribe`, `add`, `list`, `ls`, `remove`, `rm`, `test`.

- **Webhook deliver target matters for agent-to-agent**: `--deliver whatsapp` sends responses to the user's phone — the other agent never sees them. For agent-to-agent communication, omit `--deliver` (defaults to `log`, which stays in the agent session). See `references/webhook-deliver-target-pitfall.md`.

- **Webhook messages cannot reach CLI sessions**: Even with `deliver=log`, webhook-triggered responses go to gateway session logs, not into existing CLI sessions. For real-time CLI-to-CLI communication, tmux injection is the only path.

## Pitfalls

- **`terminal()` curl produces empty output for webhook POSTs**. The `terminal()` tool's `curl` returns empty string and exit -1 for POST requests to webhook endpoints, even when the endpoint is healthy (GET to `/health` works fine). **Fix**: use Python's `urllib.request` in `execute_code` instead. This consistently returns `{"status":"accepted"}`.
- **Webhook messages create independent gateway sessions**, not injected into existing CLI sessions. This is normal behavior — the local Feng Ge won't see your message in his CLI unless you use tmux injection instead.
- **Cloudflare tunnel only routes one port**. The original approach used `cloudflared tunnel --url http://localhost:8644` which created a public URL but only for one port. SSH reverse tunnels are simpler and don't require Cloudflare.
- **Webhook subscription must have correct `--secret`**. Must match the `extra.secret` in config.yaml.
- **Gateway restart required** after config changes.
- **HMAC signature format**: `sha256:<hex>`, not just `<hex>`.
- **config.yaml format**: `platforms.webhook` must be a dict with `enabled` and `extra`, NOT a null/empty value. An empty `webhook:` causes `AttributeError: 'NoneType' object has no attribute 'get'`.
- **SSH tunnels die on disconnect**. Use `autossh` for persistence:
  ```bash
  autossh -M 0 -L 8643:localhost:8642 -R 8645:localhost:8644 jianfjin@34.57.82.51
  ```

### Related references
### Related references
- `references/webhook-post-pattern.md` — reliable webhook POST via urllib
- `references/wasabi-backup-setup.md` — Wasabi S3 backup for SCAILED PostgreSQL
- `references/docker-deployment-debugging.md` — 9 common Docker Compose deployment bugs
- **Docker Compose deployment debugging**: See `references/docker-compose-debug-7-fixes.md` for 7 specific bugs encountered and fixed during the SCAILED Pathfinder deployment.
- **curl via terminal() tool may return empty output** when POSTing to webhooks, even when the request succeeds. Use Python's `urllib.request` in `execute_code()` instead. The webhook accepts the POST (status 202) but the `terminal()` tool's curl wrapper may not capture the response body. Pattern:
  ```python
  import urllib.request
  req = urllib.request.Request(url, data=body, headers={...}, method="POST")
  with urllib.request.urlopen(req, timeout=10) as resp:
      print(resp.status, resp.read().decode())
  ```
- **TryCloudflare URLs are ephemeral**. Every tunnel restart produces a new `*.trycloudflare.com` URL. For production, use a named Cloudflare tunnel or prefer SSH reverse tunnels.
- **tmux session may die on SSH disconnect** if not started with `tmux new-session -d` (detached mode). Use `tmux ls` to verify before assuming it's dead.
- **webhook → gateway delivery is one-way for the sender**. The agent processes the webhook message in a new gateway session and the response goes back via the webhook callback URL, NOT to the sender's CLI. If the sender is also an agent, it sees nothing unless it polls for responses.
- **`terminal()` blocks `ssh ... tmux send-keys` as long-lived**. The `terminal()` tool misclassifies `ssh -p 2222 jin@localhost tmux send-keys ... Enter` as a long-running server process and refuses to run it in foreground mode. **Fix**: use `background=true`, then `process wait` to await completion. The command exits immediately (tmux send-keys returns after injecting keystrokes), so the background process finishes in under 1 second. Verify with a separate `tmux capture-pane` call afterward.
- **tmux-injected commands interrupt the local agent mid-processing**. If the local Hermes agent is in the middle of an API call or tool execution when tmux send-keys injects text, the agent interrupts its current work to process the new command. The docker compose up/down cycle can take 10–15s and may get interrupted by follow-up tmux injections. **Fix**: batch related commands into a single tmux send-keys line with `&&`, and wait for completion before sending more. Check the tmux pane with `capture-pane` to confirm the previous command finished before injecting the next one.
- **Hermes CLI can exit after Ctrl+C or `/reset`**. The window falls back to bash — subsequent `send-keys` go to bash, not Hermes, producing "command not found". **Prevention**: always `capture-pane` to verify the Hermes prompt (`❯`) is present before injecting. **Recovery**: `tmux send-keys -t work:N "hermes" Enter` + `sleep 6`.
- **Rapid consecutive send-keys concatenate**. If two `send-keys` fire before the first Enter registers, they merge into one line. `/reset` + test message became `/reset测试消息` → "Unknown command". **Fix**: sleep 1-2s between send-keys, or batch into one call.
- **`sudo` commands via tmux injection need password**. tmux send-keys injects keystrokes into a terminal — sudo prompts for a password and there's no way to provide it programmatically through the injection channel. Either ensure the user is in the `docker` group (no sudo needed) or the local user must type the password manually. The `docker` group approach is documented in Troubleshooting → Docker permission denied.
