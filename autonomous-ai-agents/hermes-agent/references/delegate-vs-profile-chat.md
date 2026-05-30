# delegate_task vs profile chat -q: Personality Context Loading

**Updated:** 2026-05-29
**Key finding:** `delegate_task` does NOT load a profile's SOUL.md personality context. Only `profile chat -q` via terminal does.

## The Problem

When you need a specific profile (e.g. `shimu`, `feifei`, `demi`) to respond IN-CHARACTER — with their SOUL.md persona, memories, config.yaml model settings, and wiki — you MUST use direct profile invocation.

```python
# ❌ WRONG — agent runs as default Hermes, ignores profile's SOUL.md
delegate_task(profile="shimu", goal="Answer in character...")

# ✅ CORRECT — agent loads shimu's full profile context
terminal("shimu chat -q 'Answer in character...'")
```

## Why

`delegate_task` spawns a **subagent** of the parent session. The subagent:
- Does NOT load the specified profile's config.yaml, SOUL.md, or memories
- Runs with the parent session's model/provider/tools
- Only receives the `goal` and `context` strings you provide
- Is optimized for speed and structured output, not personality depth

`profile chat -q` (equivalent to `hermes -p shimu chat -q '...'`) launches a **full standalone Hermes instance** that:
- Loads the profile's `config.yaml` (model, provider, tools)
- Loads the profile's `SOUL.md` as system prompt
- Loads the profile's `memories/` directory
- Loads the profile's `wiki/` structure
- Uses the profile's own session history

## When to Use Each

| Method | Loads SOUL.md? | Loads Memories? | Best For |
|--------|:--------------:|:---------------:|----------|
| `delegate_task` | ❌ No | ❌ No | Technical evaluations, structured output, multi-doc generation, speed-critical tasks |
| `profile chat -q` | ✅ Yes | ✅ Yes | Roleplay, in-character responses, NSFW content, any task requiring profile-specific persona |

## NSFW & Guardrail Implication

`delegate_task` inherits the **parent session's model** (usually the user's default). If the parent uses deepseek-v4-flash, the subagent will refuse NSFW content at the provider level.

`profile chat -q` uses the **profile's configured model**. If the profile's `config.yaml` has `provider: xai` and `default: grok-4.20-0309-reasoning`, the NSFW content passes through.

See `~/.hermes/skills/productivity/inner-circle-debate/references/roleplay-nsfw-debate-pattern.md` for the full NSFW debate orchestration pattern, including model switching.

## NSFW & Guardrail Pitfalls by Model

| Model | NSFW via SOUL.md? | Notes |
|-------|:-----------------:|-------|
| deepseek-v4-pro | ❌ Rejects | Provider-level guardrail; explicit content refused even when SOUL.md explicitly authorizes it |
| deepseek-v4-flash | ❌ Rejects | Same provider-level guardrail |
| grok-4.20-0309-reasoning | ✅ Passes | xAI has no NSFW filter for prose |
| kimi-k2.6 | ✅ Passes | No content filter on this endpoint |

**Important:** A profile's SOUL.md can contain explicit NSFW instructions. If the profile uses deepseek, the model will still refuse to generate explicit content at inference time — the guardrail operates at the provider/model level, not the system prompt level. SOUL.md content is NOT a bypass mechanism.

## Implementation Delegation Pattern

Profiles can write files via `terminal` tools, enabling multi-profile code implementation workflows:

```bash
# Dispatch implementation work to a profile (background, file-writing capable)
terminal(
  command="hermes -p xiaolong chat -q '...write code to files...' --quiet -t terminal,file",
  background=true,
  notify_on_complete=true,
  timeout=900
)
```

**Key flags for code-writing tasks:**
- `--quiet` (`-Q`) — suppresses banner/spinner for clean programmatic output
- `-t terminal,file` — gives the profile session shell + file write access
- `background=true` — runs as separate process, doesn't block parent
- `notify_on_complete=true` — sends a notification when the profile finishes

**Collecting output from background profile tasks:**
```python
# Poll progress
process(session_id="proc_xxx", action="poll")

# Wait for completion (with timeout)
process(session_id="proc_xxx", action="wait", timeout=120)

# Get full output log
process(session_id="proc_xxx", action="log", limit=200)
```

**Available profiles and their aliases:**
```bash
hermes profile list                    # List all profiles
hermes profile show <name>             # Show model, alias, path
~/.local/bin/<name> == hermes -p <name>  # Profile alias wrapper
```

## Multi-Profile Parallel Implementation Workflow

For code reviews and implementation delegation to multiple persona profiles simultaneously:

1. Decompose the work into independent streams
2. Launch each profile in background via `terminal(background=True)`
3. Poll/wait for completion
4. Collect outputs and integrate

```bash
# Launch Linus (architecture review) + Guido (Python review) in parallel
terminal(command="hermes -p linus chat -q '...review...' --quiet -t terminal,file", background=true, notify_on_complete=true)
terminal(command="hermes -p guido chat -q '...review...' --quiet -t terminal,file", background=true, notify_on_complete=true)

# Wait for both, then launch implementation profile with review context
process(session_id="proc_linus", action="wait", timeout=300)
process(session_id="proc_guido", action="wait", timeout=300)

# Launch implementation profile with all review findings
terminal(command="hermes -p xiaolong chat -q '...implement...' --quiet -t terminal,file", background=true, timeout=900)
```

**Caveat:** Each `hermes -p <name>` command starts a full model warm-up (8-10s). For many quick queries, `delegate_task` is faster. Use `profile chat -q` when profile persona/SOUL.md identity is essential.

## How to Configure a Profile for NSFW Content

```yaml
# ~/.hermes/profiles/<name>/config.yaml
model:
  api_key: ''
  context_length: 65536
  default: grok-4.20-0309-reasoning   # NOT deepseek
  provider: xai                        # NOT deepseek
```

Also ensure `agent.reasoning_effort: none` in config.yaml — xAI Grok models reject the `reasoningEffect` parameter.
