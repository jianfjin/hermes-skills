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
- **Extracting alternative sources from `<source>` elements:** When an RSS `<link>` redirect loops back to Google News instead of resolving to the publisher, extract the `<source url="...">Publisher</source>` field from each `<item>` to find alternative publications covering the same story. Use `grep -oP '<source url="[^"]+">[^<]+</source>'` on the raw RSS XML. Then search those publications' sites directly for the story title.

## Publisher accessibility tiers

For automated news gathering, prefer Tier 1 sites. Tier 2 works with caution. Tier 3 requires RSS/Google News as intermediary -- go straight to those feeds rather than trying direct access.

### Tier 1 -- Fully accessible (browser + curl, no bot walls)

| Publisher | Discovery URL | Article link pattern | Notes |
|-----------|---------------|----------------------|-------|
| The Hacker News | `https://thehackernews.com/` | Search-friendly, `<article>` structure | Best source for cybersecurity + AI intersection stories. Loads instantly via browser and curl. |
| The Decoder | `https://the-decoder.com/` | `/slug/` on the-decoder.com domain | Dedicated AI news site. No anti-bot walls — works reliably via browser and curl. Good first stop for AI news roundups. Article pages have sidebar "TOP STORIES" section that surfaces additional trending stories. |\n| Ars Technica | `https://arstechnica.com/ai/` | `/ai/2026/MM/slug/`, `/tech-policy/2026/MM/slug/` | Tech policy and AI industry. Light bot detection but returns 200 with correct `<title>`. Works via browser and curl. Use `browser_console` with `Array.from(document.querySelectorAll('article h2 a')).map(a => ({title: a.textContent.trim(), href: a.href}))` to batch-extract article links from the AI category page. |
| AWS Blog | `https://aws.amazon.com/blogs/machine-learning/` | `/blogs/machine-learning/slug/` | Cloud/infrastructure AI announcements. Fully accessible. |
| BBC News | `https://www.bbc.com/news/technology` | `<a href="/news/...">` | Prepend `https://www.bbc.com`. H1 contains headline. Article pages return HTTP 200 + readable `<title>`. |
| The Guardian | `https://www.theguardian.com/technology/artificialintelligenceai` | Article pages at `/technology/YYYY/mon/DD/slug` | Article pages return HTTP 200 with proper `<title>` via curl. Reliable for verification. |
| AP News | `https://apnews.com/hub/artificial-intelligence` | `<a href="https://apnews.com/article/...">` | Hub page is accessible, but individual article pages may return "Page unavailable" via curl. Verify before presenting. |
| NPR | `https://www.npr.org/sections/technology/` | Accessible but mixed results | Try; if blocked, fall back to RSS. |

### Tier 2 -- Browser-only (JS-heavy, curl gets incomplete content)

| Publisher | Discovery URL | Notes |
|-----------|---------------|-------|
| TechCrunch | `https://techcrunch.com/category/artificial-intelligence/` | Inconsistent: may load once but time out on all subsequent browser navigation attempts within the same session. Curl returns empty. If you get a successful page load, immediately extract article URLs with `browser_console` and verify them later with curl. |

### Tier 3 -- Blocked (Cloudflare, DataDome, paywall)

Use RSS or Google News as intermediary for these. Do not attempt direct access -- it will timeout or return bot-detection pages.

| Publisher | Blocking mechanism | Workaround |
|-----------|-------------------|------------|
| Reuters | JS-required page | Use Google News RSS for story discovery. |
| Gizmodo | Browser times out, curl returns empty | Use Google News RSS for story discovery. Verify article URLs carefully; guessed URLs often return 404. |
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
| The Verge | Aggressive bot detection | Use RSS or Google News as intermediary. |\n| VentureBeat | Vercel security checkpoint | Use RSS or Google News as intermediary. Not accessible via browser or curl. |
| Techmeme | Times out via browser | Use RSS or Google News as intermediary. |

### Tier 4 -- Untested / unknown

| Publisher | Notes |
|-----------|-------|
| ZDNet | Published-RSS works (`topic/artificial-intelligence/rss.xml`, 20 items). Article HTML is JS-heavy; RSS is the reliable path. |
| The Register | May be accessible; test before relying on. |
| BleepingComputer | May be accessible; test before relying on. |

## AI/Tech RSS feeds (works without browser)

These feeds were tested and return structured XML with titles, links, and publication dates. Use them for AI news roundups when JS-heavy HTML pages are unreachable.

| Source | RSS Feed URL | Items returned | Notes |
|--------|-------------|----------------|-------|
| TechCrunch AI | `https://techcrunch.com/category/artificial-intelligence/feed/` | ~20 | Works despite article HTML having Turnstile challenges. Titles are clean; links point to canonical article URLs. |
| Wired AI | `https://www.wired.com/feed/tag/ai/latest/rss` | ~10 | Works despite article HTML being JS-heavy. |
| VentureBeat AI | `https://venturebeat.com/category/ai/feed/` | ~3 | Works despite article HTML returning 429 (Vercel checkpoint). Fewer items than others. |
| ZDNet AI | `https://www.zdnet.com/topic/artificial-intelligence/rss.xml` | ~20 | Works well. Note that ZDNet covers broad tech — not all items will be AI-specific. |
| Ars Technica AI | `https://feeds.arstechnica.com/arstechnica/ai` | Variable | Official RSS; may return fewer items than the HTML category page. Fall back to HTML + browser if needed. |

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

## Lightweight bash title verification (quick check without Python)

When you only need to confirm a URL loads and has the right title (no body extraction), use this one-liner — faster than a full parser and works from terminal/execute_code:

```bash
# Check HTTP status
curl -sL --max-time 15 -o /dev/null -w '%{http_code}' "URL"

# Extract page title
curl -sL --max-time 15 "URL" 2>/dev/null | grep -oP '<title[^>]*>.*?</title>' | head -1 | sed 's/<[^>]*>//g'
```

Combine both to verify status + title match in one script. This is the fastest path for batch-verifying news article URLs when body content isn't needed.

```bash
# Batch verify: check status and title for multiple URLs
for url in \
  "https://www.bbc.com/news/articles/abc123" \
  "https://www.theguardian.com/technology/2026/may/15/slug"; do
  status=$(curl -sL --max-time 15 -o /dev/null -w '%{http_code}' "$url" 2>/dev/null)
  title=$(curl -sL --max-time 15 "$url" 2>/dev/null | grep -oP '<title[^>]*>.*?</title>' | head -1 | sed 's/<[^>]*>//g')
  echo "HTTP $status | $title"
  echo "  $url"
  echo ""
done
```

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
