---
name: wasabi-backup
description: PostgreSQL backup to Wasabi (S3-compatible, no egress fee) via rclone — setup, backup script, cron, restore, and 4-layer verification.
version: 1.0.0
---

# Wasabi Backup — PostgreSQL via rclone

S3-compatible cloud backup for PostgreSQL. Wasabi chosen over B2 because: no egress fees on restore.

## Setup (one-time)

### 1. Create Wasabi bucket
```
wasabi.com → sign up → Create Bucket: scailed-backups
Region: eu-central-1 (Frankfurt, nearest to The Hague)
```

### 2. Install rclone
```bash
curl https://rclone.org/install.sh | sudo bash
```

### 3. Configure rclone
```bash
rclone config
# n) New remote
# name: wasabi
# type: s3
# provider: Wasabi
# access_key_id: <AK>
# secret_access_key: <SK>
# region: eu-central-1
# endpoint: s3.eu-central-1.wasabisys.com
```

### 4. Verify
```bash
rclone ls wasabi:scailed-backups/
```

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

echo "$LABEL Uploading to Wasabi..."
rclone copy "$DUMP" wasabi:scailed-backups/pg/
rclone copy "${DUMP}.sha256" wasabi:scailed-backups/pg/

echo "$LABEL Cleaning old backups..."
rclone delete --min-age 30d wasabi:scailed-backups/pg/
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
