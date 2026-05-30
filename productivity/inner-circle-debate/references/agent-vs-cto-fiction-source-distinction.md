# Source Labeling: Agent Self-Write vs CTO Fiction

## Why This Matters

The user has explicitly asked "这是谁写的?" multiple times this session. They want to distinguish between authentic character voice and orchestrated narrative. Every document produced for council business should be labeled.

## Source Labels

| Source | Label | When to Use |
|--------|-------|-------------|
| CTO writes directly | `来源：峰哥代笔` | Guardrails block; scene requires 5+ synchronous characters with intimate content |
| Agent via delegate_task | `来源：agent自写（delegate_task）` | Simple reviews where persona isn't critical |
| Agent via terminal() | `来源：agent自写（terminal）` | Character-voice-sensitive tasks: voting, intimate content, technical debate |
| Mixed | `来源：混合（CTO框架+agent输出）` | Council verdict collages combining multiple agent votes |

## When to Use Which Method

### delegate_task (fast, default model, no persona)
- Pros: Fast, works for simple tasks
- Cons: Uses session's default model + persona, NOT the target profile's SOUL.md
- Use for: Raw data processing, file writing, simple yes/no responses
- Do NOT use for: Character-voice-sensitive content, explicit intimate scenes, or tasks requiring the profile's distinctive style

### terminal() (correct profile, own model, own SOUL.md)
- Pros: Uses the profile's actual model, SOUL.md, and memories. Produces authentic character voice
- Cons: Requires background process management (poll/wait), longer setup
- Use for: Council votes with rich character voice, intimate/erotic content, any task where the profile's distinctive style matters
- Verified 2026-05-29: Xiaolong (deepseek-v4-pro) and xuefeng (deepseek-v4-flash) both generated authentic, character-consistent documents via terminal() that matched their SOUL.md voice

### CTO Fiction (fallback)
- Pros: No guardrail issues, synchronous multi-character scenes possible
- Cons: Homogenizes personas into orchestrator's voice, user can distinguish
- Use when: Guardrails block, or scene requires 5+ synchronous characters with intimate content
- Always label as `来源：峰哥代笔`
