# Docker Compose Deployment Bugs — SCAILED Pathfinder V1

Discovered during P0 e2e verification (2026-05-17) by local Feng Ge.
The core lesson: application-layer e2e tests pass does NOT mean Docker can boot.

## Bug Table

| # | Symptom | Root Cause | Fix |
|---|---------|------------|-----|
| 1 | uvicorn crash at startup | pip --no-deps skips runtime dependencies | Remove `--no-deps` from pip install |
| 2 | Python ModuleNotFoundError | pip --prefix path not in sys.path | Add `/install/lib/python3.12/site-packages` to PYTHONPATH |
| 3 | Traefik returns "no router" for all routes | Traefik v3.3 Docker client v1.24 incompatible with Docker API 1.44 | Upgrade to `traefik:v3.7` |
| 4 | All routes return 404 | ratelimit@docker middleware self-references and gets filtered by providers.docker | Remove ratelimit middleware entirely (demo doesn't need it) |
| 5 | Backend service has no route despite compose labels | Missing `traefik.enable=true` label on backend container | Add `- "traefik.enable=true"` label |
| 6 | `/api` path returns Traefik dashboard | Internal dashboard (priority 9e18) hijacks `/api` prefix | Remove `--api.insecure=true` from Traefik command |
| 7 | Frontend healthcheck never passes | `wget localhost` resolves to IPv6 but nginx only listens on IPv4 | Change to `wget http://127.0.0.1/health` |
| 8 | `/api` path doesn't reach backend correctly | `/api/...` routes need path stripping | Add StripPrefix middleware in Traefik |
| 9 | Token mismatch between compose and code | .pyc cache retained old token value across rebuilds | Force `--build` with no cache; verify token in `api/main.py` matches docker-compose DEMO_TOKEN |

## Detection Pattern

Application e2e (pytest) tests the code logic. Docker e2e tests the deployment logic.
These are two entirely separate domains. A passing test suite says nothing about Docker.

**Always verify both:**
1. `python3 -m pytest tests/` → application logic
2. `docker compose up -d --build && curl http://localhost/health && curl http://localhost/api/health` → deployment logic

## Files Affected

- `deploy/docker-compose.yml` — bugs 3,4,5,6,8
- `deploy/Dockerfile.backend` — bugs 1,2,9
- `deploy/Dockerfile.frontend` — bug 7
