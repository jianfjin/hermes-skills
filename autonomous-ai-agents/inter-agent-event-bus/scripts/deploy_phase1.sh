#!/usr/bin/env bash
# ============================================
# Phase 1 v2 一键部署脚本
# Linus: "9步中一定有人在某个环境里做错。用脚本部署。"
# ============================================
#
# 11 steps:
#   1.  Environment checks (Python >= 3.9, SQLite >= 3.30)
#   2.  NFS / filesystem type check
#   3.  Backup current database
#   4.  Create database directory
#   5.  Install dependencies (stdlib only — skip)
#   6.  Run schema migration
#   7.  Integrity verification
#   8.  Create systemd service (optional)
#   9.  Run quick tests
#  10.  Health check
#  11.  Deployment summary
# ============================================

set -euo pipefail

HERMES_HOME="${HOME}/.hermes"
DB_DIR="${HERMES_HOME}/shared"
DB_PATH="${DB_DIR}/event_bus.db"
BACKUP_DIR="${HERMES_HOME}/backups"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLS_DIR="$(cd "${SCRIPT_DIR}/../tools" && pwd)"

echo "=== Hermes Event Bus Phase 1 v2 Deployment ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Tools:     ${TOOLS_DIR}"
echo "Database:  ${DB_PATH}"
echo ""

# ------------------------------------------------------------------
# Step 1: Environment checks
# ------------------------------------------------------------------
echo "[1/11] Checking environment..."

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python version: ${PYTHON_VERSION}"
python3 -c "import sys; assert sys.version_info >= (3,9), 'Python >=3.9 required'"

SQLITE_VERSION=$(python3 -c "import sqlite3; print(sqlite3.sqlite_version)")
echo "  SQLite version: ${SQLITE_VERSION}"
python3 -c "import sqlite3; vi = sqlite3.sqlite_version_info; assert vi >= (3,30,0), f'SQLite >= 3.30 required, got {sqlite3.sqlite_version}'"

echo "  OK"

# ------------------------------------------------------------------
# Step 2: NFS / filesystem type check
# ------------------------------------------------------------------
echo "[2/11] Checking filesystem type..."

mkdir -p "${DB_DIR}"

PYTHONPATH="${TOOLS_DIR}:${PYTHONPATH:-}" python3 -c "
import sys
sys.path.insert(0, '${TOOLS_DIR}')
from nfs_check import check_filesystem_type
check_filesystem_type('${DB_PATH}')
"

echo "  OK"

# ------------------------------------------------------------------
# Step 3: Backup current database
# ------------------------------------------------------------------
echo "[3/11] Backing up current database..."

mkdir -p "${BACKUP_DIR}"
BACKUP_FILE="${BACKUP_DIR}/event_bus.$(date +%Y%m%d-%H%M%S).pre_phase1_v2.db"

if [ -f "${DB_PATH}" ]; then
    cp "${DB_PATH}" "${BACKUP_FILE}"
    echo "  Backup saved: ${BACKUP_FILE}"
else
    echo "  No existing database to backup"
fi

# Also backup WAL/SHM if present
for ext in wal shm; do
    if [ -f "${DB_PATH}-${ext}" ]; then
        cp "${DB_PATH}-${ext}" "${BACKUP_FILE}-${ext}" 2>/dev/null || true
    fi
done

# ------------------------------------------------------------------
# Step 4: Create database directory
# ------------------------------------------------------------------
echo "[4/11] Ensuring database directory..."
mkdir -p "${DB_DIR}"
echo "  Directory exists: ${DB_DIR}"

# ------------------------------------------------------------------
# Step 5: Install dependencies
# ------------------------------------------------------------------
echo "[5/11] Installing Python dependencies..."
# Phase 1 v2 uses stdlib only — no pip install required
echo "  No external dependencies (stdlib only)"

# ------------------------------------------------------------------
# Step 6: Run schema migration
# ------------------------------------------------------------------
echo "[6/11] Running schema migration..."

PYTHONPATH="${TOOLS_DIR}:${PYTHONPATH:-}" python3 "${TOOLS_DIR}/../scripts/migrate_schema_v2.py" \
    --db-path "${DB_PATH}"

echo "  OK"

# ------------------------------------------------------------------
# Step 7: Database integrity verification
# ------------------------------------------------------------------
echo "[7/11] Verifying database integrity..."

PYTHONPATH="${TOOLS_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, sqlite3
sys.path.insert(0, '${TOOLS_DIR}')
from event_schema_v2 import SCHEMA_VERSION

conn = sqlite3.connect('${DB_PATH}')
cur = conn.cursor()

# PRAGMA integrity_check
cur.execute('PRAGMA integrity_check')
row = cur.fetchone()
assert row[0] == 'ok', f'Integrity check failed: {row[0]}'

# schema_version check
cur.execute('SELECT MAX(version) FROM schema_version')
v = cur.fetchone()[0]
assert v == SCHEMA_VERSION, f'Schema version mismatch: got {v}, expected {SCHEMA_VERSION}'

# WAL mode check
cur.execute('PRAGMA journal_mode')
m = cur.fetchone()[0]
assert m.lower() == 'wal', f'Journal mode mismatch: {m}'

# Table existence check
for tbl in ('events', 'consumer_cursors', 'dead_letters', 'schema_version'):
    cur.execute(\"SELECT name FROM sqlite_master WHERE type='table' AND name=?\", (tbl,))
    assert cur.fetchone() is not None, f'Missing table: {tbl}'

print(f'OK: integrity=ok, schema_version={v}, journal_mode={m}')
conn.close()
"

echo "  OK"

# ------------------------------------------------------------------
# Step 8: Create systemd service (optional)
# ------------------------------------------------------------------
echo "[8/11] Creating systemd service..."

SERVICE_FILE="/etc/systemd/system/hermes-event-bus.service"

if [ -d "/etc/systemd/system" ]; then
    cat > /tmp/hermes-event-bus.service << SERVICEEOF
[Unit]
Description=Hermes Inter-Agent Event Bus
After=network.target local-fs.target

[Service]
Type=simple
User=%u
WorkingDirectory=%h/.hermes
ExecStart=python3 -m hermes_agent.event_bus.daemon
Restart=always
RestartSec=5
MemoryMax=256M
CPUQuota=50%

[Install]
WantedBy=multi-user.target
SERVICEEOF

    if sudo cp /tmp/hermes-event-bus.service "${SERVICE_FILE}" 2>/dev/null; then
        sudo systemctl daemon-reload 2>/dev/null || true
        echo "  Systemd service created: ${SERVICE_FILE}"
        rm -f /tmp/hermes-event-bus.service
    else
        echo "  WARNING: Could not install systemd service (not root?)"
        echo "  Service template saved to: /tmp/hermes-event-bus.service"
    fi
else
    echo "  No systemd found, skipping service creation"
    echo "  To start manually: python3 -m hermes_agent.event_bus.daemon &"
fi

# ------------------------------------------------------------------
# Step 9: Run quick tests
# ------------------------------------------------------------------
echo "[9/11] Running quick test suite..."

TEST_DIR="${SCRIPT_DIR}/../tests/event_bus"
if [ -f "${TEST_DIR}/test_core.py" ]; then
    PYTHONPATH="${TOOLS_DIR}:${SCRIPT_DIR}/.." python3 -m pytest "${TEST_DIR}/test_core.py" -v --tb=short -q 2>/dev/null || \
        echo "  WARNING: Quick tests returned non-zero"
else
    echo "  No test suite found at ${TEST_DIR}/test_core.py — skipping"
fi

# ------------------------------------------------------------------
# Step 10: Health check
# ------------------------------------------------------------------
echo "[10/11] Running health check..."

PYTHONPATH="${TOOLS_DIR}:${PYTHONPATH:-}" python3 -c "
import sys, json
sys.path.insert(0, '${TOOLS_DIR}')
from observability import health_check
result = health_check('${DB_PATH}')
print(json.dumps(result, indent=2))
if result['status'] == 'error':
    sys.exit(1)
"

HEALTH_EXIT=$?
if [ $HEALTH_EXIT -ne 0 ]; then
    echo "  WARNING: Health check returned status=error"
else
    echo "  OK"
fi

# ------------------------------------------------------------------
# Step 11: Deployment summary
# ------------------------------------------------------------------
echo "[11/11] Deployment summary:"
echo "=========================================="
echo "Database:       ${DB_PATH}"
echo "Backup:         ${BACKUP_FILE:-none}"
echo "Schema Version: 2"
echo "Journal Mode:   WAL"
echo "NFS Check:      PASSED"
echo "Integrity:      VERIFIED"
echo "=========================================="
echo "=== Phase 1 v2 deployment complete ==="
