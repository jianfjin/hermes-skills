# Docker Compose Deployment Debugging (SCAILED Pathfinder)

9 bugs encountered during Docker deployment of SCAILED Pathfinder V1.
All were infrastructure-layer issues not caught by application-layer e2e tests.

## Lesson: e2e must be two-layered

Application-layer e2e (unit tests, API tests) != deployment-layer e2e 
(Docker Compose, Traefik routing, health checks). Both must pass independently.

## Bugs Fixed

| # | Symptom | Root Cause | Fix |
|---|---------|-----------|-----|
| 1 | uvicorn crash | pip --no-deps missing deps | Remove --no-deps |
| 2 | ModuleNotFoundError | pip --prefix not in sys.path | PYTHONPATH += /install/lib/python3.12/site-packages |
| 3 | Traefik no routes | v3.3 Docker API client v1.24 incompatible with host v1.44 | traefik:v3.7 |
| 4 | Route 404 | ratelimit@docker self-referencing + filtered | Remove middleware labels |
| 5 | Backend no route | Missing traefik.enable=true label | Add label |
| 6 | /api hijacked | Internal dashboard priority 9e18 intercepts /api | Remove --api.insecure |
| 7 | Frontend unhealthy | wget localhost resolves IPv6, nginx only IPv4 | 127.0.0.1 |
| 8 | /api path loss | Frontend /api → backend needs path normalization | StripPrefix middleware |
| 9 | Token ghost | .pyc cache retains old token values | Clean rebuild + demo-token unified |
