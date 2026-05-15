# Multi-Profile Parallel Agents — Debate Pattern

## Use Case

Run multiple Hermes profiles **in parallel**, each with a different model/provider and persona,
to simulate a multi-agent debate/discussion. Useful for:
- Inner circle decision-making (simulated board of advisors)
- Adversarial review (one agent proposes, another audits)
- Multi-perspective analysis of the same topic

## Pattern Overview

```
┌─────────────────────────────────────────────────────┐
│ Profile: default (Feng Ge / CTO)                    │
│ Model: deepseek-v4-pro  │ Role: Orchestrator          │
├─────────────────────────────────────────────────────┤
│ Profile: musk (Elon Musk / CVO)                     │
│ Model: kimi-k2.6        │ Role: First Principles      │
├─────────────────────────────────────────────────────┤
│ Profile: xuefeng (Zhang Xuefeng / CSA)              │
│ Model: deepseek-v4-flash│ Role: Realism Auditor       │
└─────────────────────────────────────────────────────┘
         │                      │
         ▼                      ▼
    ┌─────────────────────────────────┐
    │ Orchestrator synthesizes        │
    │ both responses → final report   │
    └─────────────────────────────────┘
```

## Setup — Step by Step

### 1. Create profiles for each agent

Each profile inherits from `default` (preserving .env, skills, memory config), then gets its own model assignment:

```bash
# Create from default clone
hermes profile create musk --clone-from default
hermes profile create xuefeng --clone-from default

# Assign model + provider per profile
musk config set model.default kimi-k2.6
musk config set model.provider kimi-coding-cn

xuefeng config set model.default deepseek-v4-flash
xuefeng config set model.provider deepseek

# Verify
hermes profile list
musk doctor
xuefeng doctor
```

Each profile gets a CLI wrapper at `~/.local/bin/<name>` for direct access.

### 2. Choose execution mode

| Mode | Command | When to Use |
|------|---------|-------------|
| One-shot parallel | `inner-circle-debate.sh "topic"` (see `scripts/`) | Quick synchronous debate, fire-and-forget |
| Background fire-and-forget | `terminal(command="musk chat -q '...'", background=true)` | Non-blocking, collect later |
| Interactive TMUX | `tmux new-session -d -s musk 'musk'` | Real-time interaction with each agent |
| Cronjob-driven | `hermes cron create ... --model <model> --provider <provider>` | Scheduled recurring debates |

### 3. One-shot debate script

The companion script (`scripts/inner-circle-debate.sh`) launches all parallel agents with a shared topic, waits for completion, and dumps results to `/tmp/inner-circle-debate-<ts>/`.

```bash
~/.hermes/scripts/inner-circle-debate.sh "Should we use GraphRAG or LLM-Wiki for EHDS compliance?"
```

Output:
```
/tmp/inner-circle-debate-20260511_193600/
├── musk.txt       # Elon's first-principles take
├── musk_err.txt   # stderr
├── xuefeng.txt    # Zhang's realism audit
└── xuefeng_err.txt
```

### 4. Interactive mode (from parent Hermes session)

When running inside an existing Hermes session, use `terminal(background=True)` to spawn profile agents non-blockingly:

```
# Spawn both agents in parallel
terminal(command="musk chat -q 'Analyze Paperclip architecture from first principles' > /tmp/musk_out.txt 2>&1", background=true, notify_on_complete=true)
terminal(command="xuefeng chat -q 'Audit Paperclip architecture for realist traps' > /tmp/xuefeng_out.txt 2>&1", background=true, notify_on_complete=true)
```

Then read and synthesize when both complete.

## Pitfalls

- **API key isolation**: Profiles cloned from `default` share the same `.env` (API keys). If different providers need different keys, ensure all required keys are in the parent `.env` before cloning, or add them per-profile afterward.
- **Memory collision**: Each profile has independent memory. The orchestrator (Feng Ge / default) sees its own memory; spawned agents see theirs. Cross-agent context must be passed explicitly in the prompt.
- **`/reset` doesn't restart the gateway**: If a profile's gateway is running, config changes take effect on gateway restart, not `/reset`.
- **Profile wrapper discovery**: The `musk`/`xuefeng` wrappers are at `~/.local/bin/` — ensure this is in `$PATH` before calling them from scripts.

## Related

- `scripts/inner-circle-debate.sh` — One-shot launcher for 3-agent parallel debate
- `references/gateway-platform-importerror-debug.md` — Debugging platform startup failures
