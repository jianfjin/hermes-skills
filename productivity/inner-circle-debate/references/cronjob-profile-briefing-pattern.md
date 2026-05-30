# Cronjob → Council Profile Briefing Pattern

## Purpose

Schedule cron jobs that invoke council agent profiles (feifei, demi, etc.) via `terminal()` to generate independent, persona-driven daily briefings (AI news, HackerNews, etc.). Each profile speaks in its own voice, loaded from its SOUL.md and memory.

## When to Use

- User asks for daily news/briefings with a specific council member's personality
- User wants automated content delivered to a chat channel with built-in editorial voice
- Extending existing cron infrastructure with persona-driven outputs

## Architecture

```
Hermes Cron Scheduler → terminal("feifei chat -q 'prompt'") → feifei profile (SOUL.md + memory) → output → delivered to origin channel
```

Each cron job is a standalone Hermes session. The profile loads its own SOUL.md, memory files, and tools — same as if the user typed `feifei chat -q "..."` manually.

## Cron Job Spec

### Structure

```yaml
cronjob:
  name: "<profile>-<topic>-briefing"
  schedule: "0 18 * * *"         # Daily at 18:00 UTC
  deliver: "origin"               # Send back to the user's chat
  prompt: >
    Use terminal() to invoke `<profile> chat -q "Today's briefing:
    <detailed instructions>"`. The profile will generate the briefing
    in its own voice using its SOUL.md identity. Capture the full output
    and deliver it here.
  enabled_toolsets:
    - terminal                    # Required: can't invoke profile without it
    - web                         # Optional: for profiles that need web search
```

### Prompt Design Rules

1. Write the prompt as instructions to YOURSELF (the hermes agent creating the cron job), instructing IT to call `terminal()` on the `<profile> chat` command
2. The prompt for `<profile> chat` should be a second-level prompt — what you want the profile agent to say
3. Be specific about format: include placeholders (source URL, score, comment count) the profile should fill in
4. Reference the profile's SOUL.md identity in the prompt so it activates the right persona: "你是CAS首席AI科学家" for feifei, "你是Pika创始人/CCT产品视角" for demi

### Validated Examples (2026-05-27)

**feifei-ai-news-briefing** — Fei-Fei Li (CAS/Chief AI Scientist):
- Schedule: `0 18 * * *` (18:00 UTC)
- Prompt instructs hermes to call `feifei chat -q "Today's AI news briefing: browse recent AI/ML research papers and news, pick top 3 developments, analyze as Stanford HAI co-director"`
- Fei-Fei's SOUL.md activates: CAS议席 identity → academic tone, rigorous analysis, ethical lens

**demi-hackernews-briefing** — Demi Guo (CCT/Pika founder):
- Schedule: `0 18 * * *` (18:00 UTC)
- Prompt instructs hermes to call `demi chat -q "Browse today's top HackerNews posts, pick 3 most interesting, give your product founder's perspective"`
- Demi's SOUL.md activates: CCT identity → competitive, fast, founder voice

### Manual Testing

To test a new briefing job before committing it to a schedule:

Create the cron job, then manually trigger:
```
cronjob action=run job_id=<id>
```

Wait ~60s, then check:
```
cronjob action=list
```

When `last_status="ok"` and `last_run_at` has a timestamp, the output was delivered.

Note: `cronjob action=run` triggers the job asynchronously. In testing, the job may reschedule to the next available time window rather than executing immediately. The definitive test is to check for the delivered output in the conversation.

## Model Configuration

The council profile's model must be correctly configured for the briefing to succeed:

| Profile | Suggested Model | Key Config |
|---------|----------------|------------|
| feifei  | deepseek-v4-flash | Fei-Fei's SOUL.md has dual identity (CAS + fiction character). For briefings, the prompt activates CAS identity. |
| demi    | deepseek-v4-flash | Demi's SOUL.md has dual identity. For briefings, the prompt activates CCT/product founder. |

- DeepSeek profiles use `base_url: https://api.deepseek.com/v1`
- `terminal()` runs in a fresh subprocess — it does NOT inherit the parent session's state

## Pitfalls

- **Timing**: First briefing may take longer as the profile loads SOUL.md and searches its memory. ~30-60s for deepseek-v4-flash.
- **Dual-identity bleed**: If a profile's SOUL.md contains both council seat AND novel character lore (as feifei, demi, lixiaoran now do), the prompt determines which identity activates. An ambiguous prompt like "tell me about yourself" will yield a blended response. A specific prompt like "作为斯坦福HAI联合主任，分析今天的AI动态" locks the CAS identity.
- **No notify_on_complete**: Cron jobs run independently. There's no way to know when they finish except checking the delivery.
- **deliver: origin**: Output goes to the original platform (WhatsApp, CLI, etc.) where the cron job was created.
