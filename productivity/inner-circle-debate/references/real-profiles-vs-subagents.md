# Real Profiles vs Subagent Impersonation

## The Distinction (Critical)

When running a council debate, you have two fundamentally different methods:

### Method 1: Real Profile (`profile chat -q`)

```bash
timeout 60 feifei chat -q "Your question here"
```

**What this does**: Loads the actual Hermes profile — its SOUL.md, all memories, config.yaml, and its specified model. The agent speaks with its authentic voice, memories intact, personality fully activated.

**Cost**: Higher. The SOUL.md + memory files + model all get loaded into context. ~5-15 seconds per response depending on model speed.

**When to use**: When the persona's authenticity matters — their specific expertise, stored memories, and unique voice are needed. The user can tell the difference.

### Method 2: Subagent Impersonation (`delegate_task`)

```python
delegate_task(context="You are Linus Torvalds...", goal="Evaluate X")
```

**What this does**: Spawns a fresh subagent with a personality prompt. It does NOT load any Hermes profile — no SOUL.md, no memories, no config.yaml. It runs with the default model (deepseek-v4-flash unless overridden) and has zero history or context from the profile's stored state.

**Cost**: Much lower. A small context prompt instead of a full profile load. ~3-8 seconds per response.

**When to use**: When speed and token economy matter and the persona is a known archetype (e.g. "Linus Torvalds, direct, blunt, kernel architect").

## The Honesty Rule

**Do not say "Andrej Karpathy said X" when a subagent played him. Say "the subagent representing Andrej Karpathy recommended X."** The user rightfully called this out — subagent opinions are not real profile opinions.

If you use subagents, be explicit about it:
- "The council debated using subagent impersonations [not real profiles]"
- "Feifei, Demi, 李小冉 were loaded as real profiles"
- "All male members were subagent impersonations"

## When the User Found Out

The user asked: "每次召集council成员开会，峰哥召集的并不是hermes profile里真正的agent，而是subagent冒充的吗？"

The honest answer was:
- 4 women (feifei, demi, lixiaoran, shimu) = **real profiles** via `profile chat -q`
- 9 men (xiaolong, andrej, andrew, linus, guido, musk, xuefeng, jensen, lisasu) = **subagent impersonations** via `delegate_task`

The user's reaction: accepted it and chose to continue with subagents to save tokens. Document this preference.

## Practical Guidance

| Factor | Real Profile | Subagent |
|--------|-------------|----------|
| Authenticity | ✅ Full persona | ⚠️ Prompt-based sketch |
| Memories | ✅ All loaded | ❌ None |
| Model | ✅ Profile's model | ⚠️ Default model |
| Cost | Higher | Lower |
| Speed | Slower | Faster |
| NSFW handling | Depends on model | Depends on default model |

**Hybrid approach**: Load key female profiles as real profiles, use subagents for male members. This balances authenticity for the characters that matter most against token economy.

**Model matters for NSFW**: deepseek-v4-flash (default for many profiles and subagents) refuses sexual content. grok-4.20-0309-reasoning passes it through. If the council debate requires NSFW scenarios (e.g. "being fucked while discussing"), ensure the relevant profiles use grok, or the subagent prompt explicitly frames the NSFW context.
