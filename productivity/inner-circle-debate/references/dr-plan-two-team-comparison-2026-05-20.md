# DR Plan Comparison — Two-Team Pattern E Debate

**Date**: 2026-05-20
**Pattern**: Two-Design Comparison (Pattern E)
**Teams**: VM Council (6 seats) vs Local Team

## Process

1. Emperor ordered both teams to produce independent DR/backup/master-slave plans
2. VM Council convened 6 seats (Musk/Jensen/Linus/Xiaolong/Xuefeng/Dijkstra)
3. Both plans submitted, CTO synthesized comparison table
4. Emperor will adjudicate

## Key Divergence

| Dimension | VM Council | Local Team |
|-----------|-----------|------------|
| Master-slave | ❌ 6/0 against | ✅ Local→VM streaming |
| Backup target | Cloud (B2/Wasabi) | VM standby |
| Cost (3yr) | €1,816 | €12,000+ |
| Restore verification | 3-layer automated proof | Not specified |

## Council's 6 Independent Arguments Against Master-Slave

1. **Jensen (CIO)**: Single VM IOPS far below replication threshold. Save money for restore automation.
2. **Musk (CVO)**: Adds failure modes (WAL corruption, delay, conflict). One dev can't fix these.
3. **Xuefeng (CSA)**: NPV calculation — only pg_dump cron has positive NPV. Master-slave increasingly negative.
4. **Xiaolong (Eng)**: RTO<5min + ≥2 DB operators + on-call. SCAILED satisfies none.
5. **Linus (Arch)**: Replication mirrors logical corruption. Offline backups protect against it.
6. **Dijkstra (CSO)**: "Without verified restoration, you have a prayer, not a backup."

## Five Pillars of the VM Council Plan

1. **pg_dump cron daily** (L1) — full dump, `-Fc` format, 30-day cloud retention
2. **WAL archiving** (L2) — `archive_mode=on` → cloud, 7-day retention
3. **Three-layer proof** (Dijkstra) — sha256 daily, schema restore weekly, full AGE count weekly
4. **Offsite cloud** — B2/Wasabi/Hetzner Storage Box, €6/month
5. **No streaming replica** — complexity/cost exceeds benefit for €145K single-dev project
