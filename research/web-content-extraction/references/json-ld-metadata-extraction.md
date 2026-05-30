# JSON-LD Metadata Extraction

Many modern news sites (TechCrunch, Ars Technica, NYT, BBC, The Verge) embed structured
article metadata in `<script type="application/ld+json">` blocks.  This is far more reliable
than regex-based HTML parsing for extracting headlines, descriptions, publish dates, and
author names — the data is already structured and doesn't depend on DOM layout.

## Extraction pattern (Python)

```python
import json, re

with open('article.html') as f:
    html = f.read()

# Find all JSON-LD blocks
json_ld_blocks = re.findall(
    r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
    html, re.DOTALL
)

for block in json_ld_blocks:
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        continue

    # Handle both single-object and @graph array structures
    items = data.get('@graph', [data]) if isinstance(data, dict) else [data]

    for item in items:
        if not isinstance(item, dict):
            continue
        atype = item.get('@type', '')
        if 'NewsArticle' in atype or 'Article' in atype:
            print(f"Headline:   {item.get('headline', 'N/A')}")
            print(f"Published:  {item.get('datePublished', 'N/A')}")
            print(f"Modified:   {item.get('dateModified', 'N/A')}")
            print(f"Desc:       {item.get('description', 'N/A')[:200]}")
            print(f"Author:     {item.get('author', [{}])[0].get('name', 'N/A') if isinstance(item.get('author'), list) else item.get('author', 'N/A')}")
            print(f"Keywords:   {item.get('keywords', [])}")
            break
```

## When to use JSON-LD vs. other methods

| Method | Best for |
|--------|----------|
| JSON-LD extraction | Headlines, descriptions, dates, authors on modern news sites |
| RSS/Atom feeds | Discovery of trending stories across many sources |
| HN Algolia API | Tech-specific trending stories with vote counts |
| Raw HTML `<h1>`/`<title>` | Fallback when JSON-LD is absent or malformed |
| HTML article body extraction | Full-text content (JSON-LD usually omits the body) |

## Sites confirmed to carry reliable JSON-LD

- **TechCrunch** — complete `NewsArticle` in `@graph`, includes headline, description, datePublished, keywords, author
- **Ars Technica** — `NewsArticle` with full metadata
- **The Verge** — present but may require browser navigation to load the full page
- **NYT** — `NewsArticle` with extensive metadata (paywall will still block body text)

## Date recency check

When verifying "today's" stories, compare `datePublished` against the current date.
The JSON-LD date is ISO-8601 and doesn't require separate regex extraction:

```python
from datetime import datetime, timezone, timedelta
pub = datetime.fromisoformat(item['datePublished'].replace('Z', '+00:00'))
is_recent = pub > datetime.now(timezone.utc) - timedelta(days=2)
```
