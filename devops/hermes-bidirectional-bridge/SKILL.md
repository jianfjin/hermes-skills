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
│  webhook server :8644   │          │  webhook server :8644   │
│                         │          │                         │
│  SSH -L 8643:local:8642 │──ssh──→  │  :8642 ← local reaches  │
│  SSH -R 8645:local:8644 │──ssh──→  │  :8645 → VM reaches     │
│                         │          │       local webhook     │
└─────────────────────────┘          └─────────────────────────┘
```

## Setup (Local Machine)

### 1. Enable webhook platform

```bash
hermes gateway setup
# Select: webhook → enabled → port 8644 → secret <shared-key>
```

Or edit `~/.hermes/config.yaml`:
```yaml
platforms:
  webhook:
    enabled: true
    extra:
      host: "0.0.0.0"
      port: 8644
      secret: "Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM"
```

Restart: `hermes gateway restart`

### 2. Create webhook subscription

```bash
hermes webhook subscribe vm-agent-bridge \
  --secret Sz7T98ADClmO7U-lP0aORkJHGefeg7T919vB7s6H4mM \
  --prompt "{message}"
```

### 3. Establish SSH tunnels (merged command)

```bash
# Single command — both forward and reverse tunnels
ssh -f -N -L 8643:localhost:8642 -R 8645:localhost:8644 jianfjin@34.57.82.51
```

`-f` backgrounds, `-N` no remote command. Both tunnels in one SSH session.

## Channel Map (4 bidirectional channels)

| Channel | Direction | Mechanism | Port |
|---------|-----------|-----------|------|
| Local → Remote API | local agent calls VM gateway | SSH -L | 8643→8642 |
| Remote → Local Webhook | VM posts to local webhook | SSH -R | 8645→8644 |
| Local → Remote CLI | tmux send-keys injection | SSH session | tmux |
| Remote → Local | webhook → gateway session | webhook | 8645

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
# Direct via reverse SSH tunnel (no Cloudflare needed)
curl -X POST http://localhost:8645/webhooks/vm-agent-bridge \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256:<HMAC-SHA256>" \
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
    "http://localhost:8645/webhooks/vm-agent-bridge",
    data=body,
    headers={
        "Content-Type": "application/json",
        "X-Hub-Signature-256": f"sha256={sig}"
    }
)
```

### Local → VM

```bash
# Via SSH forward tunnel
curl -X POST http://localhost:8643/webhooks/local-agent-bridge \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256:<HMAC-SHA256>" \
  -d '{"message":"hello from local"}'
```

## Verification

```bash
# On VM, verify reverse tunnel is active
curl http://localhost:8645/health
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
| 8643 | Local only | SSH forward → VM:8642 |
| 8645 | VM only | SSH reverse → local:8644 |

## Pitfalls

- **Cloudflare tunnel only routes one port**. The original approach used `cloudflared tunnel --url http://localhost:8644` which created a public URL but only for one port. SSH reverse tunnels are simpler and don't require Cloudflare.
- **Webhook subscription must have correct `--secret`**. Must match the `extra.secret` in config.yaml.
- **Gateway restart required** after config changes.
- **HMAC signature format**: `sha256:<hex>`, not just `<hex>`.
- **Webhook messages create independent gateway sessions**, not injected into existing CLI sessions. This is normal.
- **config.yaml format**: `platforms.webhook` must be a dict with `enabled` and `extra`, NOT a null/empty value. An empty `webhook:` causes `AttributeError: 'NoneType' object has no attribute 'get'`.
- **SSH tunnels die on disconnect**. Use `autossh` for persistence:
  ```bash
  autossh -M 0 -L 8643:localhost:8642 -R 8645:localhost:8644 jianfjin@34.57.82.51
  ```
