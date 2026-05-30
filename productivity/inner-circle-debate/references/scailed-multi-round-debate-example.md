# SCAILED WP4 Multi-Round Council Debate Example (2026-05-15/17)

Three council debates in one session — a worked example of multi-round deliberation.

## Round 1: Frontend + Database Alternatives (5 seats)
- Topic: Vue 3 vs React/Next/Svelte/Solid; PostgreSQL vs DuckDB/SQLite
- Outcome: Vue 3 retained, thin TS; PG+AGE retained, DuckDB/SQLite rejected
- Key data: React 245K★/132M npm/week vs Vue 54K★/12M npm/week

## Round 2: Agent-D Comparison (8 seats, unanimous)
- Topic: Parliament design vs Agent-D independent proposal (docs/, 11 docs)
- Outcome: 8/8 fusion verdict
  - Absorbed: immediate-start, mock-data-first, WP data contracts, product UX
  - Retained: PG+AGE, Docker Compose, 3-module D4.1, single repo, deterministic engine
- Key data: Agent-D blueprint €260-320K vs Parliament €87.5K (Xuefeng audit)

## Round 3: Next Steps (5 seats)
- Topic: Task prioritization for Phase 0 (M1-M3)
- Outcome: Top 5 priorities + what to kill

## Lessons Learned
- **Unanimous votes happen when the CTO pre-digests all inputs.** Give agents self-contained briefs with facts already verified, not URLs to explore.
- **Kimi API congestion is real.** Musk took 16m33s in Round 2. Don't wait — proceed with the agents that finished.
- **Webhook bridge debugging consumed significant session time.** The bridge itself became a sub-project. For future agent-to-agent communication, prefer SSH tunnels over Cloudflare.
- **Agent-D's contribution was absorbed despite initial design disagreements.** The right outcome: take the good ideas (mock data, contracts, UX) and reject the over-engineering (Neo4j, K8s, AI Copilot).
