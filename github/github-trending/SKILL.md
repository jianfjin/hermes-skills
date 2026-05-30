---
name: github-trending
description: Discover trending GitHub repositories — most starred this week, popular new projects, and developer trend monitoring via the GitHub Search API.
category: github
triggers:
  - "top GitHub projects"
  - "most starred this week"
  - "trending repos"
  - "popular new repositories"
  - "github trending"
  - "what's hot on github"
---

# GitHub Trending Repositories

Discover trending and popular GitHub repositories using the public API.

## Quick Start

To find the most starred **new** repos this week:

```bash
# Replace date with 7 days ago
curl -s "https://api.github.com/search/repositories?q=created:%3E2026-05-14&sort=stars&order=desc&per_page=10" \
  -H "Accept: application/vnd.github+json" \
  -H "User-Agent: hermes-cron"
```

This returns repos created in the last 7 days, sorted by total stars — the closest proxy to "stars gained this week" available via the unauthenticated API.

## Important Caveat

The GitHub Search API does **not** expose a "stars this week" metric. The trending page (`github.com/trending`) tracks week-over-week star delta, but:
- The trending page is **client-side rendered** — direct `curl` scraping returns only the static HTML shell, not the repo data
- Third-party trending API proxies (`gitterapp`, `gh-trending-api.herokuapp.com`, etc.) are unreliable and frequently dead
- The `created:>DATE&sort=stars` query returns **new repos only**, missing established repos that may have gained thousands of stars this week

Always include this caveat when presenting results.

## Filtering Spam

New-repo search results frequently contain spam/SEO repos. Filter these out.

See `references/spam-patterns.md` for detailed patterns and keyword lists from observed spam repos.

**Quick spam signals:**
- No description, or description stuffed with keyword lists
- Suspiciously high fork ratio relative to stars (>20%)
- Generic names impersonating popular projects
- No topics, no license, single-commit repos

**Verification step:** For each candidate, call `GET /repos/{owner}/{repo}` to check license, topics, and fork ratio before including in final output.

## Verification

After identifying candidates, verify each with:

```bash
curl -s "https://api.github.com/repos/{owner}/{repo}" \
  -H "Accept: application/vnd.github+json" \
  -H "User-Agent: hermes-cron"
```

Check: `stargazers_count`, `forks_count`, `license`, `topics`, `description` quality.

## Alternative: ossinsight.io

`api.ossinsight.io/v1/trends/repos?period=past_week&limit=N` returns trending repos ranked by a composite `total_score` (activity + stars + PRs). It surfaces smaller, fast-moving projects that won't appear in the stars-sorted search. Use as a supplement when looking for rising projects beyond raw star counts.

**Period parameter:** The only confirmed working value is `past_week`. Values like `past_7_days`, `weekly`, `last_7_days`, and `week` all return validation errors.

**Response format:** Rows may arrive as JSON objects (`row["repo_name"]`) or as positional arrays with a header row at index 0. Always check `type(rows[0])` and handle both. When arrays, skip row 0 (column-name header) and zip with the column list.

**Rate limiting:** ossinsight also rate-limits (HTTP 429). Insert 2–3 second delays between calls. If you hit a 429, wait 5+ seconds before retrying with a smaller `limit`.

See `references/ossinsight-parsing.md` for response format handling and reliable parsing code.

## Output Format

For daily digest / cron output, present as:
- Ranked list with star count, description, URL, key stats (forks, license, creation date)
- Honorable mentions section for notable projects just outside top 5
- Theme summary identifying patterns across the top projects

## Pitfalls

- **Do not try to scrape `github.com/trending`** with curl/wget — it's client-rendered React and returns empty shell HTML
- **Do not rely on third-party trending APIs** — all known proxies (`gh-trending-api.herokuapp.com`, `api.gitterapp.com`, `api.github-trending.com`) are dead as of May 2026
- **Star counts from `created:` search are total stars, not weekly gain** — state this clearly
- **Spam repos appear frequently** — always filter, don't blindly trust the top N results
- The `created:` date filter uses ISO 8601 format and must be URL-encoded (`:` → `%3E`)
- **GitHub Search API is almost always rate-limited unauthenticated (HTTP 403)** — plan for this. The reliable path is: (1) try GitHub Search, expect failure → (2) use ossinsight with 3s delays between calls → (3) if both fail, search DuckDuckGo Lite for "github trending this week" blog roundups
