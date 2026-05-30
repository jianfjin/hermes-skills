# HN Front Page → Verified News Digest Workflow

Concrete step-by-step for producing a verified news roundup from HN front page trending stories.

## Pipeline

1. **Navigate**: `browser_navigate("https://news.ycombinator.com/")`
2. **Snapshot**: `browser_snapshot(full=true)` — captures the top 30 stories with titles, point counts, comment counts, author, and domain labels
3. **Filter**: scan story titles for topic keywords; prioritize by points (front-page cutoff is ~30+ points, but trending stories will be 100+)
4. **For each candidate story**: click the story title link via `browser_click(ref=title_ref)`, then run `browser_console` with `window.location.href` to extract the canonical URL after HN's redirect
5. **Navigate to canonical URL**: `browser_navigate(canonical_url)` — verify the page loads (title matches, content present, no 404)
6. **404 recovery**: if the canonical URL returns 404 or "Page Not Found", go back to HN and try the domain-label link, or search for alternative coverage of the same story
7. **Compile final digest**: numbered list with title, 2-3 sentence summary, verified direct source link

## HN URL patterns

- HN wraps all story links through its own domain; clicking a story title redirects to the real source
- `browser_console` reading `window.location.href` after the click gives the resolved canonical URL
- The domain label link (e.g., `blog.google`) goes directly to the source home domain, not the article — prefer the story title link

## Score thresholds for ranking

| Signal | Meaning |
|--------|---------|
| 500+ points | Major breaking news |
| 200-500 | High-interest story |
| 100-200 | Notable story |
| <100 on front page | Likely not top-5 candidate unless highly relevant |