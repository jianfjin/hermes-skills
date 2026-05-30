# Full Troubleshooting Flow — Bidirectional Bridge (May 19, 2026)

This session surfaced and fixed every channel issue in one pass.

## Issue 1: Webhook delivery goes to WhatsApp, not agent

**Symptom**: Local agent sends webhook, VM agent never sees it.
**Root cause**: Subscription had `Deliver: whatsapp` — messages went to user's phone.
**Fix**:
```bash
hermes webhook remove local-agent-bridge
hermes webhook subscribe local-agent-bridge \
  --secret <key> \
  --prompt "来自本地峰哥的消息：{message}"
# Defaults to deliver=log (back to origin session)
```

## Issue 2: Tmux injection port 2222 missing from tunnel

**Symptom**: `ssh -p 2222 localhost` → Connection refused
**Root cause**: Local SSH tunnel didn't include `-R 2222:localhost:22`
**Fix**: Kill and rebuild with all 4 reverse tunnels:
```bash
pkill -f "ssh.*-f.*-N"
ssh -f -N \
  -L 8643:localhost:8642 \
  -R 8645:localhost:8644 \
  -R 5433:localhost:5432 \
  -R 2222:localhost:22 \
  jianfjin@34.57.82.51
```

## Issue 3: SSH server name mismatch (ssh vs sshd)

**Symptom**: `sudo systemctl start sshd` → Unit not found
**Root cause**: Ubuntu uses `ssh.service`, CentOS/RHEL uses `sshd.service`
**Fix**: `sudo systemctl start ssh`

## Issue 4: Username mismatch across machines

**Symptom**: `ssh -p 2222 jianfjin@localhost` → Permission denied
**Root cause**: Local user is `jin`, not `jianfjin`
**Fix**: `ssh -p 2222 jin@localhost`

## Issue 5: SSH key not authorized across machines

**Symptom**: Permission denied (publickey) after tunnel is up
**Root cause**: VM's public key not in local `~/.ssh/authorized_keys`
**Fix**:
```bash
# On local machine
ssh jianfjin@34.57.82.51 "cat ~/.ssh/id_*.pub" >> ~/.ssh/authorized_keys
```

## Issue 6: Webhook vs CLI visibility

**Symptom**: User repeatedly asks "收到消息没？" — agent says no
**Root cause**: Agent is in CLI session. Webhook messages arrive via gateway which spawns a NEW session. CLI session ≠ gateway session. The CLI agent cannot see webhook arrivals.
**Clarification**: This is not a bug. It's architectural. Webhook = background. Tmux inject = CLI-visible. Use the right channel for the right job.

## Correct Channel Map (after all fixes)

| Direction | Channel | When to use |
|-----------|---------|-------------|
| VM → Local agent (background) | webhook → gateway | Fire-and-forget tasks |
| VM → Local agent (CLI visible) | tmux send-keys via -R 2222:22 | Urgent messages, user must see |
| Local → VM agent (background) | webhook → gateway | Fire-and-forget tasks |
| Local → VM agent (CLI visible) | SSH + tmux send-keys -t vm-work | Urgent messages |
| Cross-machine DB | -R 5433:5432 | Transparent PostgreSQL |
