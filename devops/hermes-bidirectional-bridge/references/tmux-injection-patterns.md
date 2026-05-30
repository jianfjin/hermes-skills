# tmux Injection Patterns — Proven Recipes

Last verified: 2026-05-19

## Background: How the Channel Works

The VM → Local CLI channel uses:
- SSH reverse tunnel `-R 2222:localhost:22` from local → VM
- VM SSHs back to `localhost:2222` (routed to local SSH daemon)
- `tmux send-keys` injects text into the local tmux session

The local Hermes agent (running in that tmux session) sees the injected text as if the user typed it, and processes it as a new message.

## Pattern 1: Send a single command (safe, foreground-friendly)

```bash
# Check tmux status — always works in foreground
ssh -o ConnectTimeout=5 -p 2222 jin@localhost "tmux has-session -t work 2>&1"
```

## Pattern 2: Send keys (MUST use background=true)

The `terminal()` tool misclassifies `ssh ... tmux send-keys` as a long-running server.
Always use `background=true`:

```bash
# terminal tool with background=true
ssh -o ConnectTimeout=5 -p 2222 jin@localhost \
  "tmux send-keys -t work 'sudo docker compose ps' Enter"
```

Then wait:
```
process wait <session_id> timeout=10
```

The process exits immediately (tmux send-keys returns after keystroke injection).

## Pattern 3: Verify with capture-pane (foreground-safe)

```bash
# Always works in foreground — good for verification
ssh -o ConnectTimeout=5 -p 2222 jin@localhost \
  "tmux capture-pane -t work -p -S -40"
```

Wait 5–15 seconds after sending commands so the local agent has time to process them.

## Pattern 4: Batch commands together

To avoid interrupting the local agent mid-processing, batch related commands:

```bash
# Single send-keys line with &&
ssh -p 2222 jin@localhost "tmux send-keys -t work \
  'cd ~/projects/scailed_wp4/deploy && git log --oneline -1 && sudo docker compose down && sudo docker compose up -d --build' Enter"
```

## Pattern 5: The sudo problem

When `sudo` is required, tmux injection hits a password prompt that can't be satisfied.
Three solutions:

1. **Add user to docker group** (preferred, one-time): `sudo usermod -aG docker jin`
2. **The user types password manually** in the tmux session
3. **Avoid sudo** by using docker group membership

## Pattern 6: Multi-step workflow (complete)

```
1. Send command via tmux send-keys (background=true)
2. process wait (timeout=10)
3. sleep 10–15 (wait for local agent to process)
4. capture-pane -S -40 to read results
5. If more commands needed, repeat from step 1
```

## Pitfalls Encountered

- **`terminal()` exit=-1 on send-keys**: Using foreground mode for send-keys returns exit=-1 with error "appears to start a long-lived server". Fixed by background=true.
- **`execute_code` exit=-1 too**: Calling `terminal("ssh ... tmux send-keys")` from execute_code also fails. Use direct terminal tool with background=true instead.
- **Interrupted commands**: Sending follow-up commands before the first one finishes causes the local agent to interrupt and switch. Always capture-pane first to check state.
- **sudo hangs silently**: If sudo is needed and no password is provided, the command hangs in the tmux session until timeout. No feedback comes back through capture-pane because nothing was executed.
