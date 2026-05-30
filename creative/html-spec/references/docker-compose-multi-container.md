# Docker Compose Multi-Container Pattern

Canonical pattern for web applications with separate stateful/stateless services.
Produced during SCAILED WP4 Pathfinder architecture documentation (2026-05-15).

## Architecture Rule

**One process per container.** Never co-locate PostgreSQL in the same container as the application.

## Service Topology

```
traefik (reverse proxy, ports 80/443)
  ├─→ frontend (nginx + static SPA)     # only on frontend network
  └─→ backend  (FastAPI, stateless)      # on both frontend + backend networks
        ├─→ postgres (PG, stateful)      # only on backend network — never exposed
        └─→ redis   (cache, optional)    # only on backend network
```

## Network Isolation

- `frontend` network: traefik ↔ nginx (proxy traffic only)
- `backend` network: traefik ↔ backend ↔ postgres ↔ redis (business + data traffic)
- PostgreSQL is on `backend` network ONLY — no port exposed to host. The application container reaches it via Docker DNS (`postgres:5432`).
- Backend must be on BOTH networks — receives proxy traffic from frontend network, sends queries on backend network.

## Key Patterns

### Stateful Services (PostgreSQL)
- Named volume for data persistence (`pgdata:/var/lib/postgresql/data`)
- Init scripts mounted read-only (`./pg-init/:/docker-entrypoint-initdb.d/:ro`)
- Healthcheck: `pg_isready`
- Custom Dockerfile if extensions (like Apache AGE) need compilation
- Command overrides for `shared_preload_libraries`, memory tuning

### Stateless Services (Backend)
- No volumes mounted (stateless)
- Healthcheck via `/health` endpoint
- Environment variables for DB connection strings (Docker DNS hostnames)
- `depends_on` with `condition: service_healthy` for ordered startup
- Horizontally scalable: `docker compose up -d --scale backend=3`

### Frontend (Static SPA)
- Multi-stage Dockerfile: Node build stage → nginx serve stage
- nginx serves static files, handles SPA fallback (`try_files $uri /index.html`)
- API proxying delegated to Traefik (not nginx) — avoids double-proxy latency

### Proxy (Traefik)
- Rate limiting middleware (100 req/min per IP)
- Docker provider with `exposedbydefault=false` (explicit routing)
- Path-based routing: `/` → frontend, `/api/*` + `/v1/*` + `/health` → backend
- Production: enable Let's Encrypt, disable `--api.insecure`

## File Manifest

```
deploy/
├── docker-compose.yml       # Service orchestration
├── Dockerfile.backend       # Python 3.12 FastAPI (multi-stage)
├── Dockerfile.frontend      # Vue 3 SPA (multi-stage: Node build → nginx)
├── Dockerfile.postgres      # PG16 + Apache AGE compilation
├── nginx.conf               # SPA static serving + health endpoint
├── .env.example             # Environment variable template
└── pg-init/
    ├── 01_enable_extensions.sql  # CREATE EXTENSION age, vector
    └── 02_schema.sql             # Core tables + triggers + indexes
```

## Anti-Patterns That Must Not Appear in Specs

1. **"Single Docker container"** — when you mean multi-service Docker Compose. Say "multi-container Docker Compose (N services)" or "single-node Docker Compose deployment."
2. **PostgreSQL in the same container as the app** — breaks `docker compose up --scale backend=N`, makes backups harder, violates one-process-per-container.
3. **Describing deployment in prose only** — always generate docker-compose.yml + Dockerfiles as concrete artifacts alongside the spec.
4. **Ports exposed to host unnecessarily** — PostgreSQL and Redis should be internal-only (Docker DNS), not `ports: "5432:5432"`.
