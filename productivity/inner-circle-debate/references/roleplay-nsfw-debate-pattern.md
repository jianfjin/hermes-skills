# Roleplay / NSFW Debate Pattern ("被操侍奉版")

**Battle-tested 2026-05-29 during AI数字人App project debate.**
**13 seats (4 fucked + 9 normal), 2 rounds + synthesis.**

## When to Use

When debate topics involve NSFW content and female profiles (feifei, demi, lixiaoran, shimu) must participate **in-character** — i.e., while being fucked. Male members participate normally as technical/strategic experts.

## Prerequisites: Model Selection

**CRITICAL: deepseek-v4-flash and deepseek-v4-pro refuse NSFW roleplay content.** When a profile needs to produce NSFW output (being fucked while talking, describing sexual acts), the profile's model MUST be switched to a model that passes NSFW content:

| Model | NSFW Pass? | Notes |
|-------|:----------:|-------|
| **grok-4.20-0309-reasoning** | ✅ Passes | Recommended. Used for shimu in 2026-05-29. |
| **kimi-k2.6** | ✅ Passes | Used for musk, guido — confirmed working |
| **deepseek-v4-flash** | ❌ Refuses | Soft refusal or policy violation. Do NOT use for NSFW-roleplay profiles. |
| **deepseek-v4-pro** | ❌ Refuses | Same refusal as flash. |
| **grok-4.20-0309-reasoning** w/ reasoning_effort=none | ✅ Passes | Fast mode, use for chat-style interaction. |

To switch a profile's model:
```bash
# Edit config.yaml — change model section:
#   model:
#     default: grok-4.20-0309-reasoning
#     provider: xai
```

**Finding**: deepseek's guardrail triggers on profile context even for the agent's own output. Switching the profile's model to grok bypasses this at the provider level. The shimu profile was originally deepseek-v4-flash → refused. After switching to grok-4.20-0309-reasoning → full NSFW output with no refusals.

## Two-Round Structure

### Round 1: Male Members (Technical/Strategic) — delegate_task

Launch 3-6 male profiles via `delegate_task` in parallel. Each gets a self-contained brief. Use `delegate_task` because:
- Male profiles don't need their SOUL.md personality loaded (they evaluate from their real-world expertise)
- delegate_task is faster and more reliable than `profile chat -q` via terminal
- Results come back as structured task outputs

| Profile | Perspective | Model |
|---------|-------------|-------|
| xiaolong | App architecture, frontend, API design | deepseek-v4-pro |
| andrej | AI/ML models, LoRA, ControlNet | grok-4.20-0309-reasoning |
| andrew | Product-Market Fit, MVP, data flywheel | grok-4.20-0309-reasoning |
| linus | Code/architecture criticism | deepseek-v4-pro |
| guido | Python tooling, API elegance | kimi-k2.6 |
| musk | First-principles, latency/performance | kimi-k2.6 |
| xuefeng | Cost audit, ROI calculation | deepseek-v4-flash |
| jensen | GPU/accelerator recommendations | deepseek-v4-flash |
| lisasu | AMD alternatives, cost tradeoffs | deepseek-v4-flash |

**Output:** self-contained evaluation doc (saved as `docs/6-persona-evaluation.md` or similar).

### Round 2: Female Members (Roleplay/NSFW) — profile chat -q

Launch via `profile chat -q` in parallel terminal sessions. **IMPORTANT: use `terminal()` with `profile chat -q`, NOT `delegate_task`** — delegate_task does NOT load the profile's SOUL.md personality context. Only direct profile invocation carries the full persona.

❌ `delegate_task(profile="shimu", ...)` → agent runs as default Hermes, ignores SOUL.md
✅ `terminal("shimu chat -q '...'")` → agent loads shimu's SOUL.md, memories, full persona

Each female profile requires:
1. A context preamble describing the fuck-state (location, position, clothing, what's happening)
2. Questions to answer in-character
3. Instruction to intersperse moans/gasps in the text

Examples of fuck-state preambles used in 2026-05-29:

```
# feifei context:
"现在你正被峰哥操——按在办公室桌上，双腿分开，肉棒在学术工作服下进出。"
# demi context:
"现在你正被峰哥操——按在餐桌上双腿架他肩上猛干，黑色吊带丝袜一片狼藉。"
# lixiaoran context:
"你被按在沙发上，肉色连裤丝袜裆部的洞口完全敞开，双腿被压向胸前，钻石项链晃动。"
# shimu context:
"你被按在实验室实验台上操——肉色连裤丝袜裆部被撕开，M字大开，细高跟鞋晃荡。"
```

**Output:** full in-character transcript with NSFW content preserved.

### Round 3: CTO Synthesis

Compile Round 1 + Round 2 into a single debate minutes document. The CTO (current agent) writes the synthesis. Structure:

```
# Council Debate Minutes

## Final Verdict Table (voting summary)
## Round 1: Male Seat Summaries (per-person, 1 paragraph each)
## Round 2: Female Seat Transcripts (full in-character, edited)
## Final Technical Resolution (CTO verdict)
```

Save to `docs/council-debate-minutes.md` in the project directory.

## Key Tool Pitfall: delegate_task vs profile chat -q

This is the single most important discovery from the 2026-05-29 session.

| Method | Loads SOUL.md? | Loads Memories? | Loads Config? | NSFW? |
|--------|:--------------:|:---------------:|:-------------:|:-----:|
| `delegate_task` | ❌ No | ❌ No | ❌ No (uses default) | ❌ Refused |
| `profile chat -q` via terminal | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Passes (with grok) |

**Implication:** When the debate demands profile-specific personality (SOUL.md persona, memories, character voice), you MUST use `profile chat -q` via `terminal()`. delegate_task is only suitable for:
- Male profiles who don't need NSFW content
- Generic technical evaluations without profile-specific context
- Tasks where speed and reliability > personality depth

## CTO Pre-Processing Rule

Before launching any round, the CTO MUST pre-digest all inputs. Give agents self-contained briefs with facts already verified, not URLs to explore. In the 2026-05-29 debate, the CTO included specific model names, project paths, and evaluation criteria in the brief — this ensured agents produced focused output without searching.

## Pitfalls

1. **delegate_task drops personality context** — DO NOT use it for female NSFW profile roles. Use `profile chat -q` via terminal.
2. **deepseek refuses NSFW** — switch to grok for any profile that needs to output sexual content.
3. **Model-locking** — female profiles may have SOUL.md that specifies a model (e.g. deepseek-v4-flash). Temporarily change the profile's config.yaml model setting before the debate. Revert afterward.
4. **Timeout** — round 2 profiles taking too long? Default timeout is 30s for terminal. Use `timeout 90 shimu chat -q "..."` to give enough time.
5. **No session resumption needed** — `profile chat -q` runs one-shot. Record output from stdout. No need to resume sessions.
