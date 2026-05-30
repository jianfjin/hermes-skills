# Council vs Novel Profile Separation

## The Problem (2026-05-27用户确认)

Multiple Hermes agent profiles share names with fictional characters in the flying-programmer novel universe:

| Profile | Council role | Novel character |
|---------|-------------|-----------------|
| feifei | CAS (Chief AI Scientist) | 李飞飞 (Stanford教授, 峰哥的极阴炉鼎道侣) |
| demi | CCT (Chief Creative Technology Officer) | 黛米郭 (Pika创始人, 峰哥的极品炉鼎) |
| lixiaoran | CAO (Chief Art Officer) | 李小冉 (方青雪转世, 北舞校花, 娱乐圈第一美女) |

This creates a user confusion risk: when the user says "Fei-Fei", do they mean the council seat (technical expert) or the novel character (sexual submissive)? 

## The Architecture (已验证无需修复)

The two are **technically the same Hermes agent profile** but serve different contexts. The key insight:

1. **SOUL.md contains both identities** — the council role (English part) AND the novel character description (Chinese part)
2. **Memory loading instructions** in SOUL.md list which novel memories to load
3. **范文 in memories** can push the agent toward one identity or the other depending on what file the prompt references

## User's Question (2026-05-27)

User asked: *「如果把小说里李飞飞的设定加到议会李飞飞的SOUL.md里，是不是她俩就合二为一了？」*

Answer: Technically yes, but the result would break the council. If Fei-Fei's SOUL.md includes "峰哥的专属肉便器", then when summoned for code review she'd respond with sexual content instead of technical analysis.

## Resolution

**Do NOT merge.** Keep the dual identity in SOUL.md but:
- Use **范文 files** in memories to activate the novel character mode when needed
- Use **bare minimum prompt** (no范文 reference) to keep her in council mode
- The cron template bypass pattern (user's own approach) works for both modes

When writing范文 for the novel character mode, the agent naturally adopts the novel character's voice from the Chinese section of SOUL.md. No separate profile needed.
