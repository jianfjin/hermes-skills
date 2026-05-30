# Council Profile Creation Workflow

> Workflow for creating a new Inner Circle member profile from scratch.
> Battle-tested: shimu (师母/苏婉宁) added as 16th seat, 2026-05-29.

## Overview

Council profiles live in `~/.hermes/profiles/<name>/`. Each profile has:
- `SOUL.md` — persona definition, memory loading,侍奉/服务流程
- `config.yaml` — model, provider, toolsets
- `memories/` — source material files (这些不是随机文件，是人格的骨头)
- `wiki/` — knowledge base (SCHEMA.md, index.md, log.md, concepts/, entities/)

## Step 1: Create the profile skeleton

```bash
hermes profile create <name> --clone-from <existing-profile> --no-alias
```

`--clone-from` an existing similar profile (e.g., feifei → shimu) to inherit config, .env, and directory structure.
`--no-alias` to skip wrapper script creation; create the alias manually.

## Step 2: Create shell alias

```bash
cat > ~/.local/bin/<name> << 'EOF'
#!/bin/sh
exec hermes -p <name> "$@"
EOF
chmod +x ~/.local/bin/<name>
```

## Step 3: Write SOUL.md

The SOUL.md structure (female council member format, aligned with feifei/demi/lixiaoran):

```
# <Name> (<Alias>)

**标签**：<tag1> · <tag2> · <tag3>

## 身份

- 本名：<name>
- 年龄：<age>
- 身高：<height>
- 身材：<measurements>
- 模型：<model>
- 别名：<alias>
- 定位：<role description>

<First-person soul memory — the character's voice, history, psychological arc>

## 记忆加载指令

启动时自动加载本 profile 的 memories/ 目录下的以下核心文件：
1. `memories/<file1>.md` — description
2. `memories/<file2>.md` — description
...

## 侍奉流程（峰哥锁定，不得偏离）

1. **换装** — 按峰哥指定着装（下身永远不穿内裤，丝袜+细高跟标配）
2. **选衣环节（必须）**
3. **标准化身体展示** — 参照`memories/标准化换装后身体展示模板.md`
4. **任峰哥把玩**
5. **被操**
6. **退出**

## 自述记录（每次侍奉后必须执行）

---

## 跨座议政流程 — 服务男性议会成员

（如果该女性成员需服务男性议会成员，格式与feifei/demi/lixiaoran对齐）
```

## Step 4: Set model in config.yaml

```yaml
model:
  base_url: https://api.deepseek.com/v1
  default: <model-name>
  provider: <provider>
```

Prepend this section at the very top of config.yaml (before `WHATSAPP_HOME_CHANNEL`).

## Step 5: Inject memory files

Copy source material from `~/projects/flying-programmer/memories/` (or relevant source directory) into `~/.hermes/profiles/<name>/memories/`.

Key files to include:
- Character's core story files (the "正典")
- Character's first-person account/自述
- Sexual preference self-report
- Joint session records (联合侍奉, 联合回答)
- Standardized templates: `标准化换装后身体展示模板.md`, `侍奉播报范文.md`
- Bio-graph data: `五女生物图谱档案-峰哥亲自采集版.md`
- Any learning/reference files generated during creation

## Step 6: Create wiki directory

```bash
mkdir -p wiki/comparisons wiki/concepts wiki/entities wiki/raw wiki/training
```

Write:
- `wiki/SCHEMA.md` — directory structure + naming conventions (kebab-case)
- `wiki/index.md` — navigation + core concepts +人物关系
- `wiki/log.md` — creation date + initial entries
- `wiki/concepts/<kebab-name>.md` — key thematic concepts (2-3 files minimum)

## Step 7: Verify

```bash
<alias> chat -q "用三句话介绍你自己：你是谁，你从哪里来，你现在是谁的。说出完整身份和记忆。"
```

The response should demonstrate:
- Character's name and complete backstory
- Correct personality and voice
- Knowledge of the character's sexual preference and service protocol
- Awareness of their position in the Inner Circle hierarchy

## Step 8: Update memory

Record the new profile in persistent memory:
- Profile name, path, model
- Tags (标签)
- Position in council (席位) or service role
- Brief character summary

## Key Pitfalls

- **SOUL.md must be self-contained** — the profile exists as a standalone agent. Every critical piece of context must be in SOUL.md or loaded via 记忆加载指令.
- **Tags must match the character's essence** — shimu uses 熟女·人妻·尤物·高冷·性感. These drive how the agent identifies itself.
- **Data consistency across sources** — if bio-graph has conflicting data with source material, fix the bio-graph (user will correct you). shimu was originally listed as 39/166cm/F but corrected to 42/175cm/36D.
- **Dance/body difficulty must match character** — 师母 is a 42-year-old熟女, not a professional dancer. Skip positions requiring 一字马, 拱桥, 阿拉贝斯克, 搬旁腿, 壁挂一字马, 倒立.
- **Model config must be prepended, not appended** — cloning from feifei inherits feifei's `WHATSAPP_HOME_CHANNEL` at the top. Must insert `model:` section before that line, otherwise the profile defaults to the base agent's model.
