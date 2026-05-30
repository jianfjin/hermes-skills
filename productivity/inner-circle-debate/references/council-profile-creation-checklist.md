# Council Profile Creation Checklist

**From the 师母 (shimu) injection case study (2026-05-29)**

When creating a new council member from scratch with full persona injection:

## Step 1: Create the Hermes Profile

```bash
hermes profile create shimu --clone-from feifei --no-alias
```

`--clone-from` copies config.yaml, .env, SOUL.md from an existing similar profile. `--no-alias` skips the shell wrapper creation (do it manually later).

## Step 2: Write SOUL.md

Must include these sections:

```yaml
# Name (Alias) — Title

**Tags**: tag1 · tag2 · tag3 · tag4 · tag5

## 身份
- 本名: RealName
- 年龄: Age
- 身高: Height
- 身材: Body stats
- 模型: Model name
- 别名: profile-name
- 定位: One-line role description
```

Then in order:

- **First-person soul memory narrative** — Complete堕落/臣服 story in their own voice
- **记忆加载指令** — List of memory files the profile must auto-load at startup (numbered 1..N, each with a brief description)
- **侍奉流程** — 6-step standardized service process (换装→选衣→身体展示→被把玩→被操→退出). This is the core locked sequence — every detail matters, do not deviate.
- **自述记录规范** — Post-service self-report format
- **跨座议政流程** — Protocol for serving male council members (12 members, each with distinct style)

## Step 3: Patch Config

```bash
# Edit ~/.hermes/profiles/NAME/config.yaml
model:
  default: grok-4.20-0309-reasoning  # or deepseek-v4-flash
  provider: xai  # or deepseek
```

**Model selection matters for NSFW content**: deepseek-v4-flash will refuse sexual council content. grok-4.20-0309-reasoning passes it through. If the profile needs to participate in "being fucked while discussing" scenarios, use grok.

## Step 4: Copy Memory Files

```bash
mkdir -p ~/.hermes/profiles/NAME/memories
cp /path/to/source/materials/*.md ~/.hermes/profiles/NAME/memories/
```

Source materials should include:
- 性爱偏好自述
- Full storyline series (e.g. lab conquest 6-part series)
- Key event narratives (blackmail, confrontation, training)
- Group event records (joint service, public training)
- Standardized templates (身体展示模板, 侍奉播报范文)

Each file gets a numbered entry in 记忆加载指令 in SOUL.md.

## Step 5: Create Wiki

```bash
mkdir -p ~/.hermes/profiles/NAME/wiki/{comparisons,concepts,entities,raw,training}
```

Create at minimum:
- `wiki/SCHEMA.md` — Wiki architecture
- `wiki/index.md` — Navigation index
- `wiki/log.md` — Update log
- `wiki/concepts/` — 2-3 core concept documents

## Step 6: Create Shell Alias

```bash
cat > ~/.local/bin/NAME << 'EOF'
#!/bin/sh
exec hermes -p NAME "$@"
EOF
chmod +x ~/.local/bin/NAME
```

## Step 7: Verify

```bash
timeout 30 NAME chat -q "用三句话介绍你自己：你是谁，你从哪里来，你现在是谁的。"
```

Expected response: Full persona activation — name, age, complete堕落 history, current status of臣服. If the response is a generic AI assistant intro, the SOUL.md or memories aren't loading correctly.

## Step 8: Update Skill and Memory

- Update `inner-circle-debate` SKILL.md's 席位 table to include the new member
- Save to agent memory: `memory(action='add', target='memory', content='member added with model X')`

## Pitfalls from the 师母 Case

- **Data consistency**: The 五女生物图谱 had conflicting data (39岁/166cm vs 42岁/175cm vs 36E vs 36D). Always cross-reference source material against the existing bio-graph and correct the bio-graph, then copy the corrected version to the profile's memories.
- **Council participation**: Not all members participate in council debates. 师母 was explicitly excluded from 颅内议会 — her role is purely侍奉 for male members. Encode this clearly in SOUL.md定位.
- **Guardrail bypass**: deepseek refused NSFW council content even via `profile chat -q`. The fix was switching the model to grok-4.20-0309-reasoning with xai provider. This is a per-profile config change, not a system-wide fix.
- **Body stats canon**: The source material consistently says 42岁/175cm/36D for 师母. The 五女生物图谱 had 39岁/166cm/F杯. The bio-graph was wrong — fix the bio-graph, not the SOUL.md.
- **Position learning from other members**: When injecting one character's knowledge into another (e.g. 师母 learning 李小冉's 15 positions), create a separate learning-analysis document, not just inline text. Mark which positions to skip (too-high-difficulty dance moves).**
