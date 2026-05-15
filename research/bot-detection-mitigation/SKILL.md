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
