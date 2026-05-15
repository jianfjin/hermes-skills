# News RSS Sources and Static-Fetch Patterns

A quick-reference for discovering and verifying news stories without relying on browser tools.

## Google News RSS (search-driven discovery)

```
https://news.google.com/rss/search?q=QUERY&hl=en-US&gl=US&ceid=US:en
```

- Replace spaces with `+`.
- Returns XML with `<item>` elements containing `<title>`, `<link>`, `<pubDate>`.
- `<link>` values are Google redirect URLs; follow them with `urllib.request` to resolve to the publisher's canonical URL.
- Google News RSS reliably returns trending stories and does not block automated requests.

## Publisher accessibility tiers

For automated news gathering, prefer Tier 1 sites. Tier 2 works with caution. Tier 3 requires RSS/Google News as intermediary -- go straight to those feeds rather than trying direct access.

### Tier 1 -- Fully accessible (browser + curl, no bot walls)

| Publisher | Discovery URL | Article link pattern | Notes |
|-----------|---------------|----------------------|-------|
| The Hacker News | `https://thehackernews.com/` | Search-friendly, `<article>` structure | Best source for cybersecurity + AI intersection stories. Loads instantly via browser and curl. |
| Ars Technica | `https://arstechnica.com/ai/` | `/ai/2026/MM/slug/`, `/tech-policy/2026/MM/slug/` | Tech policy and AI industry. Light bot detection but returns 200 with correct `<title>`. Works via browser and curl. |
| AWS Blog | `https://aws.amazon.com/blogs/machine-learning/` | `/blogs/machine-learning/slug/` | Cloud/infrastructure AI announcements. Fully accessible. |
| BBC News | `https://www.bbc.com/news/technology` | `<a href="/news/...">` | Prepend `https://www.bbc.com`. H1 contains headline. |
| AP News | `https://apnews.com/hub/artificial-intelligence` | `<a href="https://apnews.com/article/...">` | Direct absolute links. JSON-LD has `datePublished`. |
| NPR | `https://www.npr.org/sections/technology/` | Accessible but mixed results | Try; if blocked, fall back to RSS. |

### Tier 2 -- Browser-only (JS-heavy, curl gets incomplete content)

| Publisher | Discovery URL | Notes |
|-----------|---------------|-------|
| TechCrunch | `https://techcrunch.com/` | Browser times out frequently. Curl returns empty. Low reliability for automated gathering. |

### Tier 3 -- Blocked (Cloudflare, DataDome, paywall)

Use RSS or Google News as intermediary for these. Do not attempt direct access -- it will timeout or return bot-detection pages.

| Publisher | Blocking mechanism | Workaround |
|-----------|-------------------|------------|
| Reuters | JS-required page | Use Google News RSS for story discovery. |
| The Guardian | 404/block to curl | Use RSS or Google News as intermediary. |
| Politico | Cloudflare ("Just a moment...") | Use RSS or Google News as intermediary. |
| Fast Company | DataDome | Use RSS or Google News as intermediary. |
| Axios | 403 Forbidden | Use RSS or Google News as intermediary. |
| NYT | DataDome / paywall | Use RSS or Google News as intermediary. |
| Washington Post | Paywall + bot detection | Use RSS or Google News as intermediary. |
| Bloomberg | "Are you a robot?" page | Use RSS or Google News as intermediary. |
| Yahoo Finance | Blocks browser and curl | Use RSS or Google News as intermediary. |
| CNBC | Times out or blocks | Use RSS or Google News as intermediary. |
| Futurism | 404 on guessed URLs | Use Google News RSS to find canonical URLs. |
| CSO Online | 404 on guessed URLs, search times out | Use Google News RSS to find canonical URLs. |
| The Verge | Aggressive bot detection | Use RSS or Google News as intermediary. |
| Techmeme | Times out via browser | Use RSS or Google News as intermediary. |

### Tier 4 -- Untested / unknown

| Publisher | Notes |
|-----------|-------|
| ZDNet | May be accessible; test before relying on. |
| VentureBeat | May be accessible; test before relying on. |
| Wired | Likely paywalled; test before relying on. |
| The Register | May be accessible; test before relying on. |
| BleepingComputer | May be accessible; test before relying on. |

## Regex recipes for headline extraction

### BBC (from category page)
```python
matches = re.findall(
    r'<a[^>]*href="(/news/[^"]+)"[^>]*>.*?<h[23][^>]*>(.*?)</h[23]>',
    html, re.DOTALL
)
for link, title in matches:
    clean = re.sub(r'<[^>]+>', '', title).strip()
    print(f"https://www.bbc.com{link} | {clean}")
```

### AP News (from hub page)
```python
matches = re.findall(
    r'<a[^>]*href="(https://apnews.com/article/[^"]+)"[^>]*>(.*?)</a>',
    html, re.DOTALL
)
seen = set()
for link, title in matches:
    clean = re.sub(r'<[^>]+>', '', title).strip()
    if clean and len(clean) > 20 and clean not in seen:
        seen.add(clean)
        print(f"{link} | {clean}")
```

### Google News RSS
```python
items = re.findall(r'<item>.*?</item>', xml, re.DOTALL)
for item in items:
    title = re.search(r'<title>(.*?)</title>', item, re.DOTALL)
    link  = re.search(r'<link>(.*?)</link>', item, re.DOTALL)
    if title and link:
        t = title.group(1).replace('<![CDATA[', '').replace(']]>', '')
        l = link.group(1).replace('<![CDATA[', '').replace(']]>', '')
        # Resolve redirect to get canonical URL
        req = urllib.request.Request(l, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as r:
            canonical = r.geturl()
        print(f"{canonical} | {t}")
```

## Date extraction (verify recency)

```python
import re

# JSON-LD
date = re.search(r'"datePublished":"([^"]+)"', html)

# Meta tag
date = re.search(
    r'<meta[^>]*property="article:published_time"[^>]*content="([^"]+)"',
    html
)

# <time> element
date = re.search(r'<time[^>]*datetime="([^"]+)"', html)
```
