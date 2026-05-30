# Per-Profile LLM Wiki with Cron-Driven Knowledge Ingestion

Deploy personal LLM wikis inside Hermes agent profile directories, wired into daily cron jobs. Each agent grows a domain-specific knowledge base from daily briefings — knowledge compounds instead of evaporating.

## When to Use This Pattern

- You have multiple Hermes agent personas that consume daily information (news, research, trending repos)
- You want each agent to accumulate knowledge over time, not start fresh every session
- You want the agents' output briefings to reference previously learned material ("following up on our coverage of X from last week")

## Architecture

Each profile gets its own `wiki/` directory:

```
~/.hermes/profiles/<name>/
├── memories/              # Briefing output files (already existed)
├── wiki/                  # NEW — persistent knowledge base
│   ├── SCHEMA.md          # Domain conventions, tag taxonomy, page thresholds
│   ├── index.md           # Sectioned page catalog with one-line summaries
│   ├── log.md             # Append-only action log
│   ├── concepts/          # Concept/topic pages
│   ├── entities/          # Entity pages (companies, models, repos, people)
│   ├── comparisons/       # Side-by-side analyses
│   └── raw/               # Immutable briefing sources (optional)
```

## Domain-Specific Customization

Each wiki's SCHEMA.md is tailored to the agent's domain. Three archetypes from production:

### AI/ML Research (FeiFei-style)
```yaml
Domain: AI/ML research — arXiv papers, model architectures, benchmarks, training methods
Tags: model, architecture, training, inference, benchmark, alignment, reasoning, agent
Thresholds: create page when entity appears in 2+ briefings OR is central to one briefing
```

### Startup/Product Intelligence (Demi-style)
```yaml
Domain: Tech startups, products, funding, HackerNews ecosystem, market dynamics
Tags: company, product, startup, big-tech, funding, valuation, trend
Thresholds: create page when company has significant funding/launch, OR appears in 2+ briefings
```

### Open Source / Developer Tools (XiaoRan-style)
```yaml
Domain: GitHub ecosystem, open source repos, dev tools, programming languages
Tags: repo, dev-tool, ai-code, language, framework, infrastructure
Thresholds: create page for repos with 5k+ weekly stars or strategic significance
```

## Cron Job Integration

Modify the serving-stage cron job (the one that produces the final output) to add two steps:

### Step 1: Read Wiki Context (BEFORE the briefing)
Add to the cron prompt:
```
=== WIKI CONTEXT ===
Before writing, read ~/.hermes/profiles/<name>/wiki/index.md and log.md (last 15 lines).
These tell you what's already known. Use this to:
- Reference previously covered topics ("follow-up on our May 29 coverage of X")
- Enrich commentary with accumulated knowledge
```

### Step 2: Ingest Knowledge (AFTER the briefing)
Add to the cron prompt:
```
=== WIKI KNOWLEDGE INGEST ===
After writing the briefing:
1. Extract 3-5 key knowledge items from today's news
2. For each item:
   - search_files to check if entity/concept already has a page
   - If exists: read page, update with new info, bump updated date
   - If new and notable: create page with YAML frontmatter (type, tags, confidence, sources)
3. Update wiki/index.md — add new pages, update total count and date
4. Append to wiki/log.md:
   ## [YYYY-MM-DD] ingest | briefing-file.md
   - [file created/updated]: summary
```

### Toolset Requirements
The cron job needs both `terminal` and `file` toolsets for wiki operations (reading/writing markdown files, searching for existing pages).

## Backfilling Existing Data

When adding a wiki to an existing profile with previous briefing files:

1. Find all existing briefing files: `search_files` for patterns like `*briefing*`, `*简报*`
2. Read each file's content (may be interleaved with erotic roleplay narrative — extract technical data carefully)
3. Identify 3-5 notable items per file
4. Create/update wiki pages as above
5. Use `delegate_task` to parallelize backfill across multiple profiles

## Key Pitfalls

- **Don't over-create pages**: A repo with 1.2k stars and one mention should not get a page. Apply SCHEMA.md thresholds.
- **Extract from narrative**: Briefing files may have erotic roleplay wrapping. Extract technical facts from the wrapper.
- **Toolset starvation**: A cron job with only `terminal` cannot run `read_file` or `write_file` on wiki markdown files. Add `file` explicitly.
- **Cross-reference avoidance**: The cron environment is constrained — skip `[[wikilinks]]` if no other pages exist yet; add them on subsequent updates.
- **Index drift**: Always update the page count and date in index.md, and always append to log.md. These are the navigational backbone.
