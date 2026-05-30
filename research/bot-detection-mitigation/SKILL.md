---
name: bot-detection-mitigation
description: Strategies for interacting with websites that employ aggressive bot detection (e.g., Schiphol, Google).
category: research
---

# Avoiding Bot Detection on Official Sites

This skill outlines strategies for interacting with websites that employ aggressive bot detection, based on failures encountered during real-world automation attempts.

## Trigger Conditions
- When a tool call to a website returns a "Just a moment...", "One moment please", or "Unusual traffic" page.
- When `browser_navigate` results in a 403 Forbidden or a CAPTCHA page.

## Proven Workflows & Workarounds

### 0. Pre-Flight: Check for Official APIs FIRST (2026-05-22)
**Before reaching for anti-bot circumvention tools (CloakBrowser, Playwright stealth, etc.), check if the target has an official API.** Many scientific and regulatory data sources have stable, well-documented REST APIs that don't require bot circumvention at all:

| Source | Official API | Status |
|--------|-------------|--------|
| PubMed | Entrez EUtils (eutils.ncbi.nlm.nih.gov) | Free, rate-limited, no API key needed for basic use |
| ChEMBL | REST API (ebi.ac.uk/chembl/api/data) | Free, stable 10+ years |
| ClinicalTrials.gov | REST API (clinicaltrials.gov/api) | Free |
| UniProt | REST API (rest.uniprot.org) | Free |
| PDB | REST API (data.rcsb.org) | Free |
| EUR-Lex | Static documents + SPARQL endpoint | No crawling needed for small datasets |
| WHO ATC | Static published tables | Manual download |

**Council ruling (2026-05-22, 4/0):** For pharm_platform demo, CloakBrowser was unanimously rejected because all target data sources had official APIs. CloakBrowser would have added 60% failure risk (Playwright download issues, Cloudflare blocks) for zero benefit. Reserve anti-bot tools for sources that actively block automated access (national medicine registries, certain pharma company portals) — and even then, try the API first.

**Rule:** Step 0 of any data-gathering task is a 30-second check: "Does this source have a public API?" If yes, use it. If no, proceed to Step 1 below.

### 1. Detection Identification
If a page title contains "Just a moment..." or the body mentions "checking that your connection is secure," the site is using a challenge-response system (like Cloudflare or Akamai) that often blocks headless browsers.

### 2. Mitigation Strategies
If direct navigation fails, attempt the following in order:
1. **Alternative Route:** Try to find the information via a third-party aggregator or a different platform (e.g., use Google Flights instead of the airline's direct site).
2. **Search-First Approach:** Use a search engine to find a cached version of the page or a different URL path that might be less protected.
3. **Human-in-the-Loop:** If the tool fails repeatedly, explicitly inform the user about the specific "bot detection" barrier and suggest:
    - A specific direct URL.
    - A local App/Website (e.g., suggesting `DirectKorting` for Dutch petrol prices instead of scraping).
    - Using a different device/network.

### 3. Pitfalls to Avoid
- **Repeatedly Refreshing:** Do not repeatedly call `browser_navigate` to the same blocked URL in a loop; this can lead to a temporary IP ban.
- **Ignoring "Just a moment" headers:** These are clear signals that the current browser profile is detected as a bot. Do not attempt to `browser_click` elements on these pages as they are not real site content.

## Verification
- The task is considered "solved" when the information is retrieved via an alternative path or the user is provided with a viable manual workaround.
