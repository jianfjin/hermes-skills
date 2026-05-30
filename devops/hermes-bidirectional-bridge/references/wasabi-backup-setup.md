# Wasabi Backup Setup for SCAILED WP4

## Registration

1. wasabi.com → register (€6/month for 1TB)
2. Create Bucket: `scailed-backups`
3. Region: `eu-central-1` (Frankfurt, closest to The Hague)
4. Generate Access Key + Secret Key

## rclone Configuration

```bash
curl https://rclone.org/install.sh | sudo bash
rclone config
# n → name: wasabi
# type: s3 → provider: Wasabi
# access_key_id / secret_access_key from step 4
# region: eu-central-1
# endpoint: s3.eu-central-1.wasabisys.com
```

## Backup Script

```bash
#!/bin/bash
# /opt/scailed/scripts/backup.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DUMP="/tmp/scailed_${TIMESTAMP}.dump"

docker exec scailed-postgres pg_dump -U pathfinder -Fc -f "$DUMP"
sha256sum "$DUMP" > "${DUMP}.sha256"
rclone copy "$DUMP" wasabi:scailed-backups/pg/
rclone copy "${DUMP}.sha256" wasabi:scailed-backups/pg/
rclone delete --min-age 30d wasabi:scailed-backups/pg/
find /backups/pg/ -name "*.dump" -mtime +7 -delete
```

## Restore

```bash
rclone copy wasabi:scailed-backups/pg/<latest>.dump .
docker exec -i scailed-postgres pg_restore -U pathfinder -d pathfinder < <latest>.dump
```

## Why Wasabi over B2

Wasabi has no egress fees. B2 charges ~€1 per 100GB downloaded. If you ever need to restore, Wasabi doesn't meter the download.
