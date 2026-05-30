# Trend Knowledge Base Template

Create at `~/.hermes/profiles/<profile>/memories/trend-knowledge.md` before the first cron run.

```markdown
# [Profile Name] Trend Knowledge Base
# Auto-updated daily by <profile>-briefing cron job
# Tracks topics appearing 2+ times in a 5-day rolling window

## Current Hot Topics (as of YYYY-MM-DD)

_(No sustained trends yet — first run of trend tracking)_

## Format

Each entry:
### [Topic/Entity Name]
- **Category**: [domain-specific category, e.g. attention mechanism / fine-tuning / AI funding / regulation / developer tools / LLM infrastructure / embedding / multimodal / ...]
- **First Seen**: YYYY-MM-DD
- **Recent Appearances**: YYYY-MM-DD, YYYY-MM-DD, ...
- **Total**: N appearances in last 5 days
- **Trajectory**: [exploding / rising / stable / cooling]
- **Cross-Links**: [related hot topics, if any]
- **Why It Persists**: [analysis of why this topic keeps appearing — conference deadline, new breakthrough, ecosystem shift, funding wave, etc.]
```

## Profile-Specific Field Variants

### Feifei (AI research)
- Category: attention mechanism, fine-tuning, model compression, concept erasure, model merging, RL, SFT, etc.
- Trajectory: rising / stable / cooling

### Demi (Startup/Tech)
- Category: AI funding, regulation, developer tools, AI productivity, hardware, platform shift, etc.
- Trajectory: rising / stable / cooling

### XiaoRan (GitHub)
- Category: AI coding tools, LLM infrastructure, frontend, data engineering, agentic coding, etc.
- Includes Star Trajectory field: growing / stable / declining
- Trajectory: exploding / rising / stable / cooling

### ShiMu (HuggingFace Models)
- Category: open-source LLM, embedding, multimodal, image gen, reasoning, etc.
- Includes Download/Trend Trajectory field
- Trajectory: exploding / rising / stable / cooling

## Maintenance

- Updated automatically by the serving briefing cron job's STEP 0
- Topics not seen in 3+ days → marked as "cooling" with last seen date
- Topics not seen in 7+ days → archival candidate (move to wiki)
- The file should never be manually edited — only the cron job writes to it
