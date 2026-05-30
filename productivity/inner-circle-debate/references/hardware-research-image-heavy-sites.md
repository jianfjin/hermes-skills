# Extracting Hardware Specs from Image-Heavy Pre-Launch Sites

## Problem

Hardware startup websites (especially Shopify-based Kickstarter pre-launch pages) often put ALL product information in images — specs tables, feature descriptions, pricing — with almost zero text content on the page. Browser vision analysis may be unavailable (model doesn't support image input), and `document.body.innerText` returns only boilerplate waitlist CTAs.

This is common for Chinese AI hardware startups targeting global audiences via Kickstarter/Shopify.

## Solution: YouTube Reviewer Transcripts

Pre-launch hardware companies send review units to tech YouTubers. These reviewers almost always read the specs aloud on camera. A 15-minute review video transcript contains more factual product data than the entire website.

### Workflow

1. **Find reviewer videos.** Check the product website for "KOL" (Key Opinion Leader) sections with embedded YouTube links. Or search `<product name> review unboxing` on YouTube.

2. **Extract transcript.** Use the `youtube-content` skill:
   ```bash
   python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py \
     "https://www.youtube.com/watch?v=VIDEO_ID" --text-only
   ```

3. **Extract specs from transcript.** Look for:
   - Memory/RAM numbers (e.g., "80 GB of it")
   - Storage (e.g., "1 TB of SSD space")
   - Power/TDP (e.g., "30W TDP", "operate up to 60W")
   - Performance numbers (e.g., "18 tokens per second")
   - Model compatibility (e.g., "run models up to 120 billion parameters")
   - Physical dimensions/weight (e.g., "305 grams")
   - Pricing or funding model (e.g., "Kickstarter campaign")
   - Technical underpinnings (e.g., "PowerInfer", "TurboSparse")

4. **Cross-validate.** If multiple reviewers covered the product, compare transcripts — different reviewers emphasize different specs.

### Fallback: Bing Search with Curl

When Google blocks bot traffic, Bing is more permissive:
```bash
curl -s -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://www.bing.com/search?q=product+name+specs" | \
  grep -oP '(?<=<p class="b_lineclamp2">)[^<]+'
```

### Anti-Pattern: Browser-Based Research on Image-Heavy Sites

`delegate_task` with browser tools will burn through 50 tool calls (and 450+ seconds of API time) navigating a Shopify image gallery with nothing to read. The subagent will hit `max_iterations` with no output. Skip the browser entirely for these sites — go straight to YouTube.

## Worked Example

**tiiny.ai (Tiny AI Pocket Lab), 2026-05-16:**

- Website: Shopify pre-launch page, all specs in images (`20-参数表.webp`)
- Source: "Alex" reviewer video (youtube.com/watch?v=RkzCAaIV_cQ)
- Transcript extracted via youtube-content skill
- Key specs recovered: 80GB unified memory, 1TB SSD, 30W TDP, 305g weight, 120B model support, 18 tok/s, PowerInfer engine, Kickstarter funding

Without the transcript, the only recoverable fact was "portable local-AI device" from a Bing snippet.
