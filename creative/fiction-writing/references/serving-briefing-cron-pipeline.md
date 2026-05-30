# Serving Briefing Cron Pipeline

## Overview

Three daily cron briefings (飞飞 AI研究, 黛米 HackerNews, 小冉 GitHub Trending) follow a **two-stage pipeline**: raw data collection → serving format transformation. Each stage is a separate cron job, linked via `context_from`.

## Pipeline Architecture

```
                   context_from
raw-briefing ───────────────────► serving-briefing ──────► deliver: origin (WhatsApp)
(4:00 AM, deliver: local)       (4:05 AM, deliver: origin)
     │                                  │
     ▼                                  ▼
cron output dir              trend-knowledge.md
(YYYY-MM-DD*.md files)       (recurring topics, 5-day window)
```

| Job | Raw | Serving | Raw Cron Dir |
|-----|-----|---------|--------------|
| Feifei AI Research | `7167c383200d` (feifei-raw-briefing) | `43ce4756d634` (feifei-ai-news-briefing) | `~/.hermes/cron/output/7167c383200d/` |
| Demi HackerNews | `ae8fa880f817` (demi-hackernews-raw) | `532abe65b6b6` (demi-hackernews-briefing) | `~/.hermes/cron/output/ae8fa880f817/` |
| Xiaoran GitHub | `e8f0365a37b4` (lixiaoran-github-raw) | `e2513881b0cc` (xiaoran-github-trending-briefing) | `~/.hermes/cron/output/e8f0365a37b4/` |

## Model Selection: Deepseek vs Grok

### The NSFW Guardrail Asymmetry

**deepseek-v4-flash** has asymmetric NSFW handling:

| Channel | Can handle NSFW? | Evidence |
|---------|-----------------|----------|
| **Tool calls** (write_file, file writes) | ✅ YES | Writes full serving briefing to `feifei-ai-briefing-YYYYMMDD.md` successfully |
| **Direct model output** (final response) | ❌ NO | Produces `[SILENT]` when cron job expects NSFW response → nothing delivered |

This means: deepseek can **write** the serving briefing to files (via tool calls during cron job execution), but cannot **output** it as the final response that gets delivered to WhatsApp. The cron framework uses the final model response for delivery.

### Fix: Use Grok for Serving Stage

Switch the serving briefing cron job to `grok-4.20-0309-reasoning` (xAI provider), which bypasses NSFW output guardrails:

```bash
# Via hermes CLI or API
hermes cron update <serving-job-id> \
  --model '{"model":"grok-4.20-0309-reasoning","provider":"xai"}'
```

**Important**: The raw briefing jobs do NOT need grok — they produce pure text (no NSFW content) and work fine on deepseek-v4-flash. Only the serving stage (which adds erotic framing) needs the model switch.

### Identifying the [SILENT] Bug in Production

When a serving briefing cron job silently fails:

1. Check cron output: `~/.hermes/cron/output/<job-id>/latest` or the YYYY-MM-DD*.md files
2. Look for `**[SILENT]**` at the end of the output file
3. If silent: the model refused the final output (guardrail issue)
4. Check if the briefing file WAS written locally (tool calls may have succeeded):
   - `~/.hermes/profiles/feifei/memories/feifei-ai-briefing-YYYYMMDD.md`
   - `~/.hermes/profiles/demi/memories/demi-ai-briefing-YYYYMMDD.md`
   - `~/.hermes/profiles/lixiaoran/memories/lixiaoran-github-briefing-YYYYMMDD.md`
5. If file exists but delivery failed → model guardrail → switch to grok

### Pitfall: Reasoning Effort Compatibility

When switching a profile from kimi-k2.6 to `grok-4.20-0309-reasoning`, the `reasoning_effort` config must be `'none'`. Grok does NOT support `reasoning_effort` at all:

```yaml
# Profile config.yaml
model:
  model: grok-4.20-0309-reasoning
  provider: xai
  reasoning_effort: none  # NOT medium, NOT ''
```

If the profile has `reasoning_effort: medium` (default from kimi), grok fails with:
```
Error: Model grok-4.20-0309-reasoning does not support parameter reasoningEffort.
```

xAI API key comes from `XAI_API_KEY` env var. If the profile has an inline `api_key`, set it to empty string (so it falls through to the env var).

## Trend Analysis System (Added 2026-05-30)

Each serving briefing now includes a STEP 0 before the existing steps:

### How It Works

1. **Scan past raw data**: Read the raw briefing cron output dir for the last 5 calendar days
2. **Read trend knowledge base**: `~/.hermes/profiles/<name>/memories/trend-knowledge.md`
3. **Identify recurring topics**: Any paper/company/repo appearing in 2+ of the last 5 days
4. **Update trend-knowledge.md**: Add new hot topics, update counts, mark cooling topics
5. **Output "🔥 热点追踪" section**: After the 5 standard serving items, include a concise analysis of recurring topics, why they persist, and cross-topic connections

### Trend Knowledge File Format

```markdown
# FeiFei AI Research Trend Knowledge Base
# Auto-updated daily by feifei-ai-news-briefing cron job

## Current Hot Topics (as of YYYY-MM-DD)

### [Topic Title]
- **Category**: [e.g., attention mechanism / fine-tuning / model compression]
- **First Seen**: YYYY-MM-DD
- **Recent Appearances**: YYYY-MM-DD, YYYY-MM-DD
- **Total**: N appearances in last 5 days
- **Trajectory**: [rising / stable / cooling]
- **Cross-Links**: [related hot topics, if any]
- **Why It Persists**: [analysis]
```

### Trend Knowledge Files Per Profile

| Profile | File Path |
|---------|-----------|
| Feifei | `~/.hermes/profiles/feifei/memories/trend-knowledge.md` |
| Demi | `~/.hermes/profiles/demi/memories/trend-knowledge.md` |
| Xiaoran | `~/.hermes/profiles/lixiaoran/memories/trend-knowledge.md` |

### Cross-Topic Connection Examples

The trend analysis should look for relationships between recurring topics:

- **Feifei (AI Research)**: Multiple papers on model efficiency (Parallax attention + KOFF decomposition + model merging) → all address the same meta-problem from different angles
- **Demi (HackerNews)**: Groq funding + AI productivity paradox + coding agent debate → inference infrastructure buildout vs application-layer ROI tension
- **Xiaoran (GitHub)**: claude-code + compound-engineering-plugin + twentyhq/twenty → agentic coding ecosystem maturing from standalone tools to plugin networks

### When "热点追踪" Is Empty

If nothing recurred in the last 5 days, output: `本期无持续热点` and move on.

## Raw Data Source for Trend Analysis

The serving briefing jobs have `enabled_toolsets: ["terminal", "file"]` which allows reading past raw data files. The raw briefing outputs are stored as YYYY-MM-DD*.md files in the cron output directories listed above.

Reading technique (in prompt):
```
Read past raw briefing outputs from ~/.hermes/cron/output/<raw-job-id>/
Use terminal/file tools to list and read YYYY-MM-DD*.md files from the last 5 calendar days
Skip files that contain only cron job header/instruction lines with no actual content
Extract headlines, topics, and key entities from each day
```

## Cron Job Prompt Structure

Each serving briefing prompt follows this structure:

1. **Delivery instructions** (auto-prepended by cron framework)
2. **[STEP 0] Trend analysis** — scan past data, update trend-knowledge.md, prepare 热点追踪 output
3. **[STEP 1] Wiki context** — read wiki/index.md and wiki/log.md for accumulated knowledge
4. **[STEP 2] Format template** — read `侍奉播报范文.md`, produce 5-item serving briefing
5. **[STEP 3] Wiki knowledge ingest** — update wiki with today's new entities/concepts

The `context_from` injection (raw briefing output) appears between the delivery instructions and STEP 0.
