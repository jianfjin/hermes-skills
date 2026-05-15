# Hacker News Algolia API — Quick Reference

**Preferred for: trending discovery, date-range filtering, full-text search.**
This is the better API when you need to find recent/hot stories by topic rather than just reading the current front page.

Base URL: `https://hn.algolia.com/api/v1/`

## Endpoints

| Endpoint | Behavior |
|----------|----------|
| `search?query=...` | Search by relevance, default sort: **points** (trending first) |
| `search_by_date?query=...` | Search sorted by **date** (newest first) |

## Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `query` | Full-text search across titles (URL-encoded) | `AI+OR+LLM+OR+OpenAI` |
| `tags` | Item type filter | `story` (excludes comments, polls, jobs) |
| `numericFilters` | Filter by numeric fields | `points%3E50,created_at_i%3E1747094400` |
| `hitsPerPage` | Max results (default 20) | `30` |

## numericFilters syntax

URL-encoded operators: `>` = `%3E`, `<` = `%3C`, `>=` = `%3E%3D`.

- `points%3E50` — only stories with >50 points
- `created_at_i%3E1747094400` — only stories after epoch timestamp
- Combine with comma: `points%3E50,created_at_i%3E1747094400`

## Response Fields (per hit)

| Field | Type | Meaning |
|-------|------|---------|
| `title` | string | Story title |
| `url` | string | External URL (null for self-posts) |
| `points` | int | Upvote points |
| `num_comments` | int | Comment count |
| `created_at` | string | ISO 8601 timestamp |
| `created_at_i` | int | Unix epoch timestamp |
| `objectID` | string | HN item ID |
| `author` | string | Submitter username |

**No second hydration request needed** — all metadata is in the search response.

## Epoch Timestamp Calculation

When filtering by date, compute epoch timestamps in UTC:

```python
from datetime import datetime, timezone

# May 14, 2026 00:00:00 UTC
ts = int(datetime(2026, 5, 14, 0, 0, 0, tzinfo=timezone.utc).timestamp())
# → 1778716800

# Use in query:
# created_at_i%3E1778716800  → stories after May 14
```

## Example: Find Trending AI Stories

```bash
# Fetch recent AI stories with >20 points from last 3 days
curl -s 'https://hn.algolia.com/api/v1/search_by_date?query=AI&tags=story&numericFilters=points%3E20,created_at_i%3E1778457600&hitsPerPage=50' \
  -o /tmp/hn_ai.json
```

```python
import json

with open('/tmp/hn_ai.json') as f:
    data = json.load(f)

ai_keywords = ['ai', 'llm', 'gpt', 'openai', 'gemini', 'claude', 'anthropic',
               'chatbot', 'machine learning', 'neural', 'copilot', 'nvidia',
               'model', 'inference', 'training', 'agent', 'rag', 'generative',
               'chatgpt', 'mistral', 'llama', 'deepseek', 'diffusion']

for h in data['hits']:
    title = h.get('title', '')
    url = h.get('url', '') or f"https://news.ycombinator.com/item?id={h['objectID']}"
    if any(kw in title.lower() for kw in ai_keywords):
        print(f"[{h['points']}pts | {h['num_comments']}cm] {title}")
        print(f"  {url}")
```

## Differences from Firebase API

| Feature | Algolia | Firebase |
|---------|---------|----------|
| Full-text search | ✅ | ❌ |
| Date-range filtering | ✅ (`created_at_i>EPOCH`) | ❌ (must fetch all, filter client-side) |
| Sort by points or date | ✅ | ❌ (fixed order per endpoint) |
| All metadata in one call | ✅ | ❌ (need 1 call per item) |
| Rate limits | 10,000 req/hour | None (but slow for many items) |
