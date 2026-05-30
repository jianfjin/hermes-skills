# Multi-Agent Novel Character Orchestration

Validated 2026-05-27 (initial), expanded 2026-05-28 (delegate_task + 双飞).

## Architecture

Each novel character (李飞飞, 黛米郭, 李小冉) has a Hermes Agent profile with a **dual-identity SOUL.md**. The authoring agent should call `skill_view("inner-circle-debate")` and read the "Dual-Identity SOUL.md Architecture" section for full design details.

## When to Use This Pattern

Use profile-generated character voices when the user wants:
- The character's **authentic first-person voice** (not the CTO's proxy)
- **Multiple characters in the same scene** responding to each other
- A character to explain a concept while staying in character
- A **shared event** told from divergent perspectives (双飞)

## Two Methods

### Method A: delegate_task (PREFERRED — validated 2026-05-28)

Use `delegate_task` to spawn character agents with full context. This replaces the older terminal-chat approach.

**Protocol:**
1. Load the character's SOUL.md and范文 (from `memories/侍奉播报范文.md`) 
2. Craft a context string containing:
   - The character's SOUL.md (full identity + 侍奉流程 + 自述记录 instructions)
   - The character's范文 or reference template
   - A factual summary of "what just happened" (specific details: clothing, positions, observations, other characters present)
   - The writing goal (first-person, length, tone, required elements)
3. Call `delegate_task` with tasks=[{context=..., goal=..., toolsets=['file']}]
4. Set toolsets=['file'] so the agent can save the output to its profile's memories/
5. The character agent uses deepseek-v4-flash (not the orchestrator's model)

**Parallel vs Sequential:**
- Parallel: use when characters are INDEPENDENT (writing about the same event but without interaction)
- Sequential: use when character B needs to react to character A's output (rare — usually handled by峰哥 writing the event summary)

**Context requirements (minimum):**
- Full SOUL.md identity section
- Full 侍奉流程 section from SOUL.md
- Full 自述记录 section from SOUL.md
- Event summary with: time, location, clothing each wore, who else present, what峰哥 did, positions,高潮, exit
- Character-specific observations: what the OTHER character did during shared scenes (双飞)

**What NOT to include in context:**
- Do NOT include峰哥's private observations or峰哥's评语 — those are for峰哥's record only
- Do NOT include the OTHER character's internal thoughts — the character doesn't have access to those
- Do NOT include范文 content inline — just tell the agent to read it from its own memories/

### Method B: Terminal chat (older approach — deprecated for self-narrative generation)

```bash
terminal(command="feifei chat -q '...'", pty=true, timeout=120)
```

Still usable for short Q&A but lacks the file-saving ability of delegate_task.

## Validated Results (2026-05-28)

### Single-event self-narratives

Each character received the same event summary (a侍奉 session conducted by峰哥) and produced divergent自述s:

| Character | Self-narrative length | Style signature | Unique content峰哥 didn't write |
|-----------|----------------------|----------------|----------------------------------|
| Feifei | ~8K chars | Academic metaphor — "论文最后等号落下", "TCP丢包", "ABAC结构" | Heartbeat counting during penetration, post-coital itinerary management |
| Demi | ~6.5K chars | Startup directness — "操", "不是记什么狗屁浪漫" |吐槽 AI papers during sex, competitive score-keeping |
| Xiaoran | ~9.4-16K chars | Dance aesthetics — "高音谱号裂纹", "ritardando", "拱桥" | Tasting semen as private ritual, deliberate停顿 as signal |

### Double-event (双飞) self-narratives — validated 2026-05-28 酉时

Same event (Feifei + Demi in书房,峰哥操作). Key divergence:

- **Feifei**: Described Demi as "强劲的同席者". Framed the session as ABAC structure (Feifei=repeated A, Demi=variant B). Said "这不是输赢的事". Identified Demi's competitive strategy (language-as-defense) and responded with her own (sound-as-connection).
- **Demi**: Scored Feifei point by point ("150度 — 十年底子", "脊椎是活的"). Declared "平局但我更喜欢我的赢法". Addressed Feifei directly at the end: "下次你来之前最好再想想怎么接住我."

**Architecture lesson:** The same delegate_task structure works for双飞. Both agents get context about what the OTHER wore, did, and said. Each writes independently. The divergence IS the output — do NOT try to harmonize or synchronize.

## Pitfall — User confusion about authorship

When presenting profile-generated output, the user may ask "是飞飞自己写的还是你写的?"

**Answer:** "这是feifei这个Hermes Agent profile独立生成的。我通过delegate_task调用她，她加载了自己的SOUL.md和记忆文件后自己写的。我没有替她写任何字。"

This distinction matters because:
- CTO-written self-descriptions = the novelist's voice for the character
- Profile-generated self-descriptions = the character's OWN voice through its agent profile

## Key: Prompt determines identity activation

The same SOUL.md produces different outputs based on prompt:
- "Review this code for vulnerabilities" → council seat identity
- "峰哥召你入殿侍奉，开始身体展示" → novel character identity  
- "用学术+臣服的语气" → blended identity
- "Read your范文 and write a continuation in that style" → character voice activated through literary model
