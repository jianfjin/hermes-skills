# Mock Upstream REST Services — aiohttp Dual-Role Pattern

## When to use

When building Docker Compose mock services for upstream REST APIs (WP2/WP3/WP8 data providers) and the consuming Pathfinder/Backend adapter needs to fetch from them via HTTP.

## Why aiohttp

| Requirement | Why aiohttp |
|-------------|-------------|
| Mock servers (<80 lines each) | `aiohttp.web` — minimal route → JSON |
| Async client in Pathfinder | `aiohttp.ClientSession` — native async/await |
| Single dependency | One library covers both server and client |
| FastAPI-compatible | FastAPI uses Starlette, same async ecosystem |
| No extra HTTP stack | httpx is fine but redundant; requests is blocking |

## Architecture

```
mocks/                              pathfinder/adapters/
├── Dockerfile.mocks                upstream.py
├── wp2_stakeholders.py (aiohttp.web)    class UpstreamClient:
├── wp3_roadmap.py (aiohttp.web)             __init__(wp2_url, wp3_url, wp8_url)
├── wp8_rules.py (aiohttp.web)               fetch_stakeholders() → aiohttp.get()
└── fixtures/*.json                          fetch_roadmap() → aiohttp.get()
                                             fetch_rules() → aiohttp.get()
```

## Docker Compose snippet

```yaml
wp2-mock:
  build: services/mock/Dockerfile.mocks
  command: python wp2_stakeholders.py
  ports: ["8102:8080"]
  healthcheck: curl -f http://localhost:8080/health
  networks: [backend]
```

## aiohttp server template (~50 lines)

```python
from aiohttp import web
import json
from pathlib import Path

async def health(request):
    return web.json_response({"status": "ok"})

async def get_all(request):
    data = json.loads(Path("fixtures/wp2_data.json").read_text())
    return web.json_response(data)

app = web.Application()
app.router.add_get("/health", health)
app.router.add_get("/api/v1/stakeholders", get_all)
web.run_app(app, port=8080)
```

## aiohttp client adapter (~120 lines)

```python
import aiohttp

class UpstreamClient:
    def __init__(self, wp2_url, wp3_url, wp8_url):
        self.urls = {"wp2": wp2_url, "wp3": wp3_url, "wp8": wp8_url}
        self._session = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args):
        await self._session.close()

    async def fetch_stakeholders(self):
        async with self._session.get(f"{self.urls['wp2']}/api/v1/stakeholders") as resp:
            return await resp.json()
```

## Transition to real APIs

One env var change, zero code change:

```bash
# Demo: mock containers
WP2_API_URL=http://wp2-mock:8080/api/v1

# Production: real WP services
WP2_API_URL=https://scailed-consortium.eu/wp2/api/v1
```

## Cost

| Task | Lines | Est. |
|------|-------|------|
| wp2 mock server | ~50 | 0.5d |
| wp3 mock server | ~60 | 0.5d |
| wp8 mock server | ~60 | 0.5d |
| Dockerfile + compose | ~30 | 0.5d |
| 3 fixture JSON files | ~200 | 0.5d |
| UpstreamClient adapter | ~120 | 1d |
| Integration + tests | ~80 | 0.5d |
| **Total** | **~600** | **4.5d** |
