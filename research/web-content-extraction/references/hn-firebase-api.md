# Hacker News Firebase API – Quick Reference

Base URL: `https://hacker-news.firebaseio.com/v0/`

## Endpoints

| Endpoint | Returns |
|----------|---------|
| `topstories.json` | ~500 top story IDs (int array), ordered by rank |
| `newstories.json` | ~500 newest story IDs |
| `beststories.json` | ~500 "best" story IDs |
| `askstories.json` | ~200 Ask HN story IDs |
| `showstories.json` | ~200 Show HN story IDs |
| `jobstories.json` | ~200 job story IDs |
| `item/<id>.json` | Story / comment / poll / job object |
| `user/<id>.json` | User profile object |

## Item fields (story)

| Field | Type | Meaning |
|-------|------|---------|
| `id` | int | Unique item ID |
| `type` | string | `"story"`, `"comment"`, `"job"`, `"poll"`, `"pollopt"` |
| `by` | string | Username of submitter |
| `time` | int | Unix timestamp of creation |
| `title` | string | Story title |
| `url` | string | External URL (omitted for Ask HN) |
| `text` | string | Self-post text, HTML-encoded (Ask HN, Show HN) |
| `score` | int | Upvote points |
| `descendants` | int | Total comment count |
| `kids` | int[] | Top-level comment IDs |
| `deleted` | bool | Optional |
| `dead` | bool | Optional |

## Example flow (Python)

```python
import json, urllib.request

# 1. Get top story IDs
with urllib.request.urlopen(BASE + "topstories.json") as r:
    ids = json.loads(r.read())[:5]

# 2. Hydrate each story
for sid in ids:
    with urllib.request.urlopen(BASE + f"item/{sid}.json") as r:
        story = json.loads(r.read())
        print(story["title"], story.get("url"), story["score"])
```

## Rate limits

None enforced by Firebase, but be polite.  Sequential requests are fine for < 50 items.
