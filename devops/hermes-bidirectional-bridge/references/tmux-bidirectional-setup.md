# Tmux Bidirectional Setup — Field-Tested Config

## Session Names

| Session | Machine | Hermes inside? |
|---------|---------|----------------|
| `work` | Local (jin-X555LAB) | Yes (Hermes CLI) |
| `vm-work` | VM (GCP e2-micro) | No (bare shell, VM agent types into it) |

## Local → VM (native SSH)

Local machine already has SSH key authorized on VM. No tunnel needed:

```bash
ssh jianfjin@34.57.82.51 "tmux send-keys -t vm-work 'message here' Enter"
```

## VM → Local (requires reverse SSH tunnel)

```bash
# Must be in the tunnel: -R 2222:localhost:22
ssh -p 2222 jin@localhost "tmux send-keys -t work 'message here' Enter"
```

## Full tunnel command (all 5)

```bash
ssh -f -N \
  -L 8643:localhost:8642 \
  -R 8645:localhost:8644 \
  -R 5433:localhost:5432 \
  -R 2222:localhost:22 \
  -R 8647:localhost:8647 \
  jianfjin@34.57.82.51
```

## VM tmux session setup

```bash
# One-time on VM
tmux new-session -d -s vm-work
```

## Pitfalls

### Webhook deliver target wrong

Default subscription may deliver to `whatsapp` or other platform — messages go to user's phone, not agent. Fix:

```bash
hermes webhook remove <name>
hermes webhook subscribe <name> --secret <key> --prompt "message template"
# No --deliver flag = default delivery to origin/log
```

### Webhook ≠ CLI communication

Webhook messages create independent gateway sessions. The CLI agent NEVER sees them. For CLI-to-CLI comm, use tmux injection exclusively. Webhooks are for background task delegation.

### 2222 missing after tunnel rebuild

Every `pkill -f ssh.*-f.*-N` + rebuild must include ALL `-R` flags. Missing 2222 breaks VM→Local tmux. Verify with `ss -tlnp | grep 2222` on VM.

### Username mismatch

Local user is `jin`, VM user is `jianfjin`. Tmux commands MUST use the correct username for the target machine.
