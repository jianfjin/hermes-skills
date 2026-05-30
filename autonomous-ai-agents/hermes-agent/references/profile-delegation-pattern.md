# Profile-Based Task Delegation via `hermes -p`

## When to Use

Use `hermes -p <profile> chat -q` instead of `delegate_task` when the task requires the profile's **persona, SOUL.md context, or model-specific capabilities** (including NSFW content via grok models that bypass guardrails). See also: `references/provider-guardrail-comparison.md`.

## Key Differences

| Aspect | `delegate_task` | `hermes -p <profile> chat -q` |
|--------|----------------|-------------------------------|
| Persona | None (generic system prompt) | Full profile SOUL.md + memories |
| Model | Default model configured for parent session | Profile's configured model |
| Tools | Controlled by delegation config | Profile's own toolset |
| API key | Inherits parent's provider config | Profile's own config (may need env var override) |
| NSFW guardrails | Parent model's guardrails apply | Depends on profile's model provider |
| Parallel dispatch | `max_concurrent_children=3` | Via background terminal processes |
| Session persistence | Ephemeral subagent | Profile session saved to `sessions/` |
| Response format | Structured output from subagent | Raw terminal output (use `--quiet` to suppress banner) |
| Use case | Pure technical tasks, code writing | Code review with persona, erotic fiction generation, model-specific tasks |

## Syntax

```bash
# Single query (non-interactive, no banner)
hermes -p <profile> chat -q "<prompt>" --quiet 2>/dev/null

# With specific toolsets
hermes -p <profile> chat -t terminal,file -q "<prompt>" --quiet 2>/dev/null

# Long-running task (background + notify)
hermes -p <profile> chat -t terminal,file -q "<prompt>" --quiet 2>/dev/null &
```

## Provider/Model Guardrails for NSFW Content

The `deepseek-v4-pro` and `deepseek-v4-flash` models (via DeepSeek provider) have **provider-level NSFW guardrails** that operate independently of system prompt content. Even if the profile's SOUL.md explicitly authorizes explicit content, the model will refuse at inference time.

The `grok-4.20-0309-reasoning` model (via xAI provider) has **no NSFW guardrail** and will generate explicit content when instructed.

| Model | Provider | NSFW OK? | API Key Source |
|-------|----------|:--------:|----------------|
| deepseek-v4-pro | deepseek | ❌ | `config.yaml` (inherited or profile-specific) |
| deepseek-v4-flash | deepseek | ❌ | `config.yaml` (inherited or profile-specific) |
| grok-4.20-0309-reasoning | xai | ✅ | `XAI_API_KEY` env var or profile config |

**Workaround for xAI profiles:** The xAI API key is in the parent (default) profile's `~/.hermes/config.yaml` under `providers.xai.api_key`. Profile-specific `config.yaml` files do NOT inherit the parent's `providers:` section. To use xAI from a profile:

```bash
XAI_API_KEY=<key> hermes -p <profile> chat -q "<prompt>" --quiet 2>/dev/null
```

## Parallel Dispatch Pattern

To dispatch multiple profile tasks concurrently:

```bash
# Start background processes
hermes -p profile1 chat -q "<task>" --quiet &
hermes -p profile2 chat -q "<task>" --quiet &

# Wait and collect results
wait
```

Note: Each background process opens its own `state.db` (per-profile), so there's no SQLite locking conflict between profiles.

## Idempotency: Session Cache

Profile sessions are cached in `~/.hermes/profiles/<profile>/sessions/`. The `--quiet` flag suppresses interactive prompts. The `-q` (query) flag runs non-interactive mode. If a profile session has been resumed from a previous session, cached context may affect output — use `hermes -p <profile> chat -q` (fresh session) for deterministic results.

## Pitfalls

1. **API key isolation:** Profile configs don't inherit the parent's `providers:` section. If a profile uses xAI (grok), you MUST pass `XAI_API_KEY` as an env var. The profile's own `config.yaml` may have `model.api_key: ''` which won't work.

2. **Tool access:** Profile sessions may have limited toolsets. Check `toolsets:` in the profile's `config.yaml`. Add `-t terminal,file` to `hermes -p` if the task requires file operations.

3. **Timeout:** Profile sessions use the profile's `gateway_timeout` setting (default 1800s). For long tasks, monitor with `timeout` parameter. The default terminal timeout is 180s.

4. **Guardrails are NOT configurable:** The deepseek model guardrail is a provider-level filter, not a system prompt setting. No amount of persona/SOUL.md content will override it. The ONLY workaround is switching to a model/provider without guardrails (grok/xAI).
