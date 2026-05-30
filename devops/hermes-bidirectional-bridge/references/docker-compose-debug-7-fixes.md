# Docker Compose Deployment — 7 Bugs Found and Fixed

SCAILED Pathfinder V1 Docker Compose deployment. 5 containers: traefik, frontend (nginx+React), backend (FastAPI), postgres (PG16+AGE), redis.

All bugs found during 2026-05-17 deployment verification by local Feng Ge on Ubuntu laptop.

## Bug 1: uvicorn crash — missing dependencies
- **Symptom**: Backend container starts then immediately exits. `uvicorn` crashes with `ModuleNotFoundError`.
- **Root cause**: `pip install --no-deps` skips transitive dependencies. Some packages need their own deps at runtime.
- **Fix**: Remove `--no-deps` from `Dockerfile.backend`, line 27.
- **File**: `deploy/Dockerfile.backend`

## Bug 2: Python can't find installed packages
- **Symptom**: `ModuleNotFoundError` for packages that ARE installed.
- **Root cause**: `pip install --prefix=/install` puts packages in `/install/lib/python3.12/site-packages/` which is NOT in `sys.path` by default.
- **Fix**: Add `/install/lib/python3.12/site-packages` to `PYTHONPATH` ENV in `Dockerfile.backend`.
- **File**: `deploy/Dockerfile.backend` line 40

## Bug 3: Traefik v3.3 Docker client too old
- **Symptom**: Traefik can't communicate with Docker daemon. Error: `Docker client API version 1.24 is too old, minimum supported is 1.44`.
- **Root cause**: Traefik v3.3 bundles an outdated Docker client library that doesn't support the host's Docker API version.
- **Fix**: Upgrade Traefik from `v3.3` to `v3.7`.
- **File**: `deploy/docker-compose.yml` line 42

## Bug 4: All routes return 404
- **Symptom**: Traefik is running but every route returns 404.
- **Root cause**: The `ratelimit@docker` middleware references itself, and the Traefik Docker provider filters out middlewares that reference unknown routes. This cascades to ALL routers being dropped.
- **Fix**: Remove all `ratelimit@docker` middleware references from Traefik command args and service labels.
- **File**: `deploy/docker-compose.yml` lines 53, 63-65, 80, 85

## Bug 5: Backend has no routes
- **Symptom**: Frontend routes work, but `/api/*` returns 404 or no route.
- **Root cause**: Backend service has no `traefik.enable=true` label. Traefik Docker provider has `exposedbydefault=false`, so services without explicit enable labels are completely ignored.
- **Fix**: Add `traefik.enable=true` label to the backend service.
- **File**: `deploy/docker-compose.yml` backend section

## Bug 6: `/api` routes hijacked by Traefik internal dashboard
- **Symptom**: Traefik internal dashboard takes priority over application routes. Requests to `/api/*` hit the dashboard instead.
- **Root cause**: `--api.insecure=true` enables Traefik's internal API/dashboard with priority 9e18 (highest possible). This starves all Docker-provided routers at any priority level.
- **Fix**: Remove `--api.insecure=true` from Traefik command args. For debugging, use `traefik.healthcheck` instead.
- **File**: `deploy/docker-compose.yml` line 47

## Bug 7: Frontend healthcheck fails
- **Symptom**: Frontend container marked unhealthy, `wget` healthcheck fails.
- **Root cause**: `wget http://localhost/health` resolves to IPv6 `::1`, but nginx only listens on IPv4 `0.0.0.0:80` inside the container.
- **Fix**: Change healthcheck from `localhost` to `127.0.0.1`.
- **File**: `deploy/Dockerfile.frontend` healthcheck line

## Lessons

1. **e2e verification must include deployment layer**, not just application layer. Unit tests and API tests passed, but Docker-specific issues only surfaced at deploy time.
2. **Traefik Docker provider is sensitive to label completeness**. Missing `traefik.enable=true` with `exposedbydefault=false` is silent failure.
3. **Always test healthchecks on the actual container networking**. `localhost` vs `127.0.0.1` matters when IPv6 is available.
4. **Rate limiting is a V2 concern**. Adding it too early creates cascading configuration failures.
