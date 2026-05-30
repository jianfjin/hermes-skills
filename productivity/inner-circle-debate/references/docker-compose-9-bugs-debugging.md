# SCAILED Pathfinder — Docker Compose 7-Bug Debugging Playbook

Deployed 2026-05-17 by local Feng Ge. All 7 bugs were deployment-layer issues that application-layer tests (pytest) could never catch.

## Bug Table

| # | Symptom | Root Cause | Fix |
|---|---------|-----------|-----|
| 1 | uvicorn crash on boot | pip --no-deps skipped transitive deps | Remove --no-deps from Dockerfile |
| 2 | ModuleNotFoundError for installed pkgs | pip --prefix puts pkgs outside sys.path | PYTHONPATH add /install/lib/python3.12/site-packages |
| 3 | Traefik: "no router for /" | v3.3 uses Docker API v1.24, host has v1.44 | traefik:v3.3 → v3.7 |
| 4 | All routes return 404 | ratelimit@docker middleware self-references + gets filtered | Remove ratelimit middleware entirely |
| 5 | "no router for /api" | backend container missing traefik.enable=true label | Add label to backend service |
| 6 | /api routes return Traefik dashboard | --api.insecure internal dashboard has priority 9e18, hijacks /api prefix | Remove --api.insecure |
| 7 | frontend healthcheck never passes | wget localhost resolves to IPv6 ::1, nginx binds IPv4 0.0.0.0 only | wget 127.0.0.1 |

Plus 2 follow-ups found in later iterations:
| 8 | /api path stripped | Frontend calls /api/v1/... but backend expects /v1/... | StripPrefix middleware in Traefik |
| 9 | token phantom values | .pyc bytecode cache retained old demo token | Force rebuild + unify to demo-token |

## Root Cause Analysis Patterns

### pip --no-deps is dangerous for multi-stage Docker builds
The `--no-deps` flag works in the builder stage when the fallback `|| pip install pkg1 pkg2 ...` explicitly lists all packages. But if requirements.txt has packages not in the fallback list, their deps are silently missing. **Recommendation**: never use `--no-deps` in Docker builds unless paired with an exhaustive fallback list.

### pip --prefix requires explicit PYTHONPATH
`pip install --prefix=/install` puts packages in `/install/lib/python3.12/site-packages/` which is NOT in Python's default search path. Must set `PYTHONPATH=/install/lib/python3.12/site-packages:...` in the runtime stage.

### Traefik Docker provider version lock
Traefik's Docker provider uses the host's Docker API version. If the Traefik image is older than the host's Docker daemon, the provider silently fails with no routes. **Always pin Traefik version to match or exceed Docker API version.**

### Traefik middleware self-referencing
`traefik.http.middlewares.ratelimit.ratelimit.average=100` defines a middleware, and `--entrypoints.web.http.middlewares=ratelimit@docker` references it. But if the middleware label is on the same container that references it, Traefik filters it out. **Don't self-reference middleware in the same service definition.**

### api.insecure dashboard priority hijack
`--api.insecure=true` creates an internal router with priority 9e18 that matches `/api` prefix before any user-defined routers. **Never use --api.insecure in production or when /api is a route prefix.**

### Docker healthcheck IPv4/v6 mismatch
`wget localhost` inside a container resolves to IPv6 `::1` on many systems. If nginx binds `0.0.0.0:80` (IPv4 only), the healthcheck connects to IPv6 and fails. **Always use 127.0.0.1 in Docker healthchecks, not localhost.**

## Prevention: Two-Layer E2E Testing

Application-layer tests (pytest) verify code logic. They do NOT verify:
- Container networking
- Traefik routing
- Healthcheck behavior
- Docker Compose service dependencies
- PYTHONPATH/PATH environment inheritance

**Mandatory deployment-layer verification for every commit that touches deploy/ or Dockerfile.*:**
```bash
cd deploy && docker compose up -d --build && sleep 10
curl -f http://localhost/health
curl -f http://localhost/api/health
docker compose ps  # all services Up (healthy)
```
