# ossinsight API Response Parsing

The ossinsight trending API (`api.ossinsight.io/v1/trends/repos`) returns rows in
one of two formats — **check `type(rows[0])` before processing**.

## Format A: Object rows (most common)
```python
rows = [{"repo_id": "1148788086", "repo_name": "mattpocock/skills", ...}, ...]
# Process directly:
for row in rows:
    name = row["repo_name"]
```

## Format B: Array rows with header (occasional)
```python
rows = [["repo_id", "repo_name", ...], [1148788086, "mattpocock/skills", ...], ...]
# Skip row 0, zip with column list:
columns = [c["col"] for c in data["data"]["columns"]]
for row in rows[1:]:
    repo = dict(zip(columns, row))
    name = repo["repo_name"]
```

## Reliable handling pattern
```python
rows = data["data"]["rows"]
columns = [c["col"] for c in data["data"]["columns"]]

if isinstance(rows[0], dict):
    repos = rows  # already objects
elif isinstance(rows[0], list):
    repos = [dict(zip(columns, r)) for r in rows[1:]]  # skip header

for repo in repos:
    print(repo["repo_name"], repo["stars"], repo["total_score"])
```

## Rate limiting
- ossinsight returns HTTP 429 when throttled
- Insert 2–3 second `time.sleep()` between calls
- On 429, wait 5+ seconds and retry with a smaller `limit` parameter
- The `period` parameter **must** be `past_week` — other values like `past_7_days` or `weekly` fail validation
