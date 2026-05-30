# SCAILED Pathfinder Docker Deployment — 7 Bugs Debugging Playbook

2026-05-17: Local Feng Ge (hermes-asus.datawego.nl) deployed the full Docker Compose stack and found 7 bugs spanning Dockerfile, Traefik routing, and container networking. All bugs were in the deployment layer — the application layer tests (13/13 pass) never touched any of these.

## Bug Summary

| # | Symptom | Root Cause | Fix | File |
|---|---------|-----------|-----|------|
| 1 | `uvicorn` crash on startup | `pip install --no-deps` skipped transitive deps | Remove `--no-deps` flag | `Dockerfile.backend` |
| 2 | `ModuleNotFoundError` for installed packages | `pip --prefix=/install` not in sys.path | Add `/install/lib/python3.12/site-packages` to `PYTHONPATH` | `Dockerfile.backend` |
| 3 | Traefik "No router found" for all services | Traefik v3.3 Docker provider incompatible with Docker API v1.44 (v1.24 client) | Upgrade to `traefik:v3.7` | `docker-compose.yml` |
| 4 | `/api` and `/v1` routes return 404 | `ratelimit@docker` middleware self-referenced + filtered by Docker provider | Remove ratelimit middleware entirely | `docker-compose.yml` |
| 5 | Backend has no Traefik route | Missing `traefik.enable=true` label on backend service | Add label to backend | `docker-compose.yml` |
| 6 | Frontend `/api/*` requests captured by Traefik internal dashboard | `--api.insecure=true` dashboard runs at priority 9e18, hijacks all routes | Remove `--api.insecure` | `docker-compose.yml` |
| 7 | Frontend healthcheck never passes (unhealthy) | `wget http://localhost/health` resolves to IPv6 `::1`; nginx listens on IPv4 only | Change to `wget http://127.0.0.1/health` | `Dockerfile.frontend` |

## Root Cause Patterns

### 1. pip --no-deps is poison in multi-stage builds
`--no-deps` skips transitive dependencies. In a `pip install --prefix=/install` setup, if `requirements.txt` lists only `fastapi` but `fastapi` needs `starlette`, the build succeeds but the runtime crashes. The fallback `pip install ...` list was manually maintained and drifted from `requirements.txt`.

**Fix**: Never use `--no-deps` in Docker builds. Let pip resolve the full tree.

### 2. --prefix installs need explicit PYTHONPATH
`pip --prefix=/install` puts packages in `/install/lib/python3.12/site-packages/` but Python doesn't search there by default. `PATH` covers binaries; `PYTHONPATH` covers imports. Both must be set.

### 3. Traefik Docker provider version lock
Traefik's Docker provider communicates with the Docker daemon's API. Traefik v3.3 shipped with an older Docker client library that couldn't parse responses from Docker API v1.44. Traefik v3.7 resolved this. Always pin Traefik to the latest patch within a major version.

### 4. Traefik middleware cannot self-reference from Docker labels
The `ratelimit@docker` middleware was defined as Docker labels on the `traefik` service itself, then referenced in `--entrypoints.web.http.middlewares` on the same service. This creates a circular reference that the Docker provider filters out at startup. Middleware applied at the entrypoint level must be defined in a static file configuration, not Docker labels.

**Fix for rate limiting in Docker Compose**: Define middleware in a `traefik.yml` static config file mounted as a volume, OR apply it per-router (not at entrypoint level).

### 5. `exposedbydefault=false` requires explicit labels on EVERY routed container
When `--providers.docker.exposedbydefault=false` is set, only containers with `traefik.enable=true` get routes. Forgetting this label on the backend means the API routes defined on the frontend's labels point to a service Traefik doesn't know about.

### 6. `--api.insecure` dashboard routes at insane priority
Traefik's internal API dashboard registers at priority `9e18` (9 × 10^18) — higher than any user-defined router. When the dashboard is enabled, its catch-all route captures requests before user-defined routers can process them. On a single-port setup (only `:80`), this means `/api/*` goes to the dashboard, not your application.

**Fix**: Remove `--api.insecure` entirely. Use `traefik` service logs (`docker compose logs traefik`) for debugging instead of the dashboard.

### 7. `localhost` in Docker containers resolves to IPv6 `::1` before IPv4 `127.0.0.1`
In many Docker base images, `/etc/hosts` maps `localhost` to both `::1` and `127.0.0.1`, but `getaddrinfo()` prefers IPv6. If the application (nginx) only listens on `0.0.0.0` (IPv4), `wget http://localhost/...` fails because it tries `::1` first. Always use `127.0.0.1` in Docker healthchecks and internal service URLs.

## Post-Deployment Verification Checklist

After `docker compose up -d`:
```bash
# 1. All containers running
docker compose ps

# 2. All healthchecks passing
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# 3. Traefik has discovered routes
curl -s http://localhost:80/health

# 4. Frontend serves static files
curl -s http://localhost:80/

# 5. API endpoints respond
curl -s -H "Authorization: Bearer demo-token" http://localhost:80/v1/questionnaires

# 6. Logs are clean (no router-not-found spam)
docker compose logs traefik | grep -c "router-not-found"
```

## Lessons for e2e Verification

The application-layer tests (13/13 pytest) tested the Python code paths — models, solver, rules, API handlers — but NONE of them exercised Docker networking, Traefik routing, or container healthchecks. **e2e verification must be done in two layers**:

1. **Application layer**: pytest (unit + integration)
2. **Deployment layer**: `docker compose up -d` + HTTP smoke tests against `localhost:80`

Finding #1-#7 all live in the deployment layer and would never be caught by application tests. This is why the M3 execution plan's P0 task (1.5 e2e Docker boot) was so critical.
