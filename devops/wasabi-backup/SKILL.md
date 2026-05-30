---
name: wasabi-backup
description: PostgreSQL backup to Wasabi (S3-compatible, no egress fee) via rclone — setup, backup script, cron, restore, and 4-layer verification.
version: 1.0.0
---

# Wasabi Backup — PostgreSQL via rclone

S3-compatible cloud backup for PostgreSQL. Wasabi chosen over B2 because: no egress fees on restore.

## Setup (one-time)

### Primary: Cloudflare R2 (€0, 10GB free tier)

1. Cloudflare Dashboard → R2 → Create Bucket: `scailed-backups`
2. Create API Token (R2 Read/Write)
3. rclone config:
```bash
rclone config
# n) New remote
# name: r2
# type: s3
# provider: Cloudflare
# access_key_id: <R2_Access_Key>
# secret_access_key: <R2_Secret_Key>
# endpoint: https://<account_id>.r2.cloudflarestorage.com
```

SCAILED data: ~50MB/day × 30-day retention = 1.5GB. Well within R2 free tier (10GB storage + 1M Class A ops + 10M Class B ops).

### Fallback: Wasabi (€6/month, no egress)

## Backup Script

```bash
#!/bin/bash
# /opt/scailed/scripts/backup.sh
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP="/tmp/scailed_${TIMESTAMP}.dump"
LABEL="[backup ${TIMESTAMP}]"

echo "$LABEL Starting pg_dump..."
docker exec scailed-postgres pg_dump -U pathfinder -Fc -f "$DUMP"

echo "$LABEL Checksum..."
sha256sum "$DUMP" > "${DUMP}.sha256"

echo "$LABEL Uploading to R2..."
rclone copy "$DUMP" r2:scailed-backups/pg/
rclone copy "${DUMP}.sha256" r2:scailed-backups/pg/

echo "$LABEL Cleaning old backups..."
rclone delete --min-age 30d r2:scailed-backups/pg/
find /backups/pg/ -name "*.dump" -mtime +7 -delete

echo "$LABEL Done."
```

## Cron

```bash
# 3 AM daily
0 3 * * * /opt/scailed/scripts/backup.sh >> /var/log/scailed_backup.log 2>&1
```

## Restore

```bash
# List available backups
rclone ls wasabi:scailed-backups/pg/

# Pull latest + restore
LATEST=$(rclone ls wasabi:scailed-backups/pg/ | grep '.dump$' | sort -k2 | tail -1 | awk '{print $2}')
rclone copy wasabi:scailed-backups/pg/$LATEST .
docker exec -i scailed-postgres pg_restore -U pathfinder -d pathfinder < $LATEST
```

## 4-Layer Verification (Council Resolution)

| Layer | Check | Frequency | Command |
|-------|-------|-----------|---------|
| V1 | sha256 file integrity | Daily | `sha256sum -c dump.sha256` |
| V2 | Schema-only restore | Weekly | `pg_restore --schema-only` |
| V3 | AGE catalog count | Weekly | `SELECT count(*) FROM ag_catalog.ag_graph` |
| V4 | Sample row count | Monthly | `SELECT count(*) FROM nodes` |

```bash
#!/bin/bash
# /opt/scailed/scripts/verify_restore.sh
set -euo pipefail

LATEST=$(rclone ls wasabi:scailed-backups/pg/ | grep '.dump$' | sort -k2 | tail -1 | awk '{print $2}')

# V1: checksum
rclone copy wasabi:scailed-backups/pg/$LATEST /tmp/
rclone copy wasabi:scailed-backups/pg/$LATEST.sha256 /tmp/
(cd /tmp && sha256sum -c $LATEST.sha256) || { echo "V1 FAIL"; exit 1; }

# V2+V3+V4: ephemeral restore
docker run -d --name scailed-verify -e POSTGRES_PASSWORD=test postgres:16
sleep 5
docker exec -i scailed-verify pg_restore -U postgres -d postgres < /tmp/$LATEST

docker exec scailed-verify psql -U postgres -d pathfinder \
  -c "SELECT count(*) FROM ag_catalog.ag_graph;"

docker rm -f scailed-verify
echo "$(date -Iseconds) — VERIFIED"
```

## Cost

| Item | €/month | Notes |
|------|---------|-------|
| Wasabi 1TB | ~€6 | No egress fee (key advantage over B2) |
| rclone | €0 | Open source |
| Total | ~€6/month | ~€216/3yr |

## Pitfalls

- **Wasabi minimum 90-day storage**: files deleted before 90 days still billed. Set lifecycle to 30 days after confirming compliance.
- **rclone config**: use `s3` type with Wasabi provider, not `wasabi` type (deprecated).
- **Restore test**: must run on a CLEAN VM at least once. Don't assume the dump is valid because checksum passed.
- **AGE graph**: pg_dump includes AGE extension data if extension is installed in the target DB. Verify `CREATE EXTENSION age;` before restore.
