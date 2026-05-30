"""dead_letter — Dead-letter queue and overflow archiving.

Conditions for dead-letter migration (Linus: "每一种选择都是架构决策"):
  1. retry_count >= max_retries  — exhausted retries
  2. created_at + ttl_seconds < now  — TTL expired
  3. consumer explicitly marks dead

Overflow auto-archiving:
  - events > 1,000,000 rows → archive processed events older than 7 days
  - disk usage > 80% → clean archived dead letters older than 30 days
"""

from __future__ import annotations

import logging
import os
import sqlite3
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from connection import EventBusWriter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dead-letter migration SQL (idempotent)
# ---------------------------------------------------------------------------

SQL_MIGRATE_ONE = """
    INSERT OR IGNORE INTO dead_letters(
        event_id, source_agent, event_type, payload,
        original_created_at, dead_reason, retry_count, consumer_id
    )
    SELECT
        event_id, source_agent, event_type, payload,
        created_at, ?, retry_count, ?
    FROM events
    WHERE event_id = ?;

    UPDATE events SET status = 'dead' WHERE event_id = ?;
"""

SQL_MIGRATE_EXPIRED = """
    INSERT OR IGNORE INTO dead_letters(
        event_id, source_agent, event_type, payload,
        original_created_at, dead_reason, retry_count, consumer_id
    )
    SELECT
        event_id, source_agent, event_type, payload,
        created_at, 'TTL_EXPIRED', retry_count, NULL
    FROM events
    WHERE status != 'processed'
      AND status != 'archived'
      AND created_at < datetime('now', '-' || CAST(? AS TEXT) || ' seconds')
      AND event_id NOT IN (SELECT event_id FROM dead_letters);

    UPDATE events SET status = 'dead'
    WHERE status != 'processed'
      AND status != 'archived'
      AND created_at < datetime('now', '-' || CAST(? AS TEXT) || ' seconds');
"""

SQL_ARCHIVE_PROCESSED = """
    INSERT OR IGNORE INTO dead_letters(
        event_id, source_agent, event_type, payload,
        original_created_at, dead_reason, retry_count, consumer_id
    )
    SELECT
        event_id, source_agent, event_type, payload,
        created_at, 'ARCHIVED_OVERFLOW', retry_count, NULL
    FROM events
    WHERE status = 'processed'
      AND created_at < datetime('now', '-7 days');

    DELETE FROM events
    WHERE status = 'processed'
      AND created_at < datetime('now', '-7 days');
"""

SQL_CLEAN_DEAD_ARCHIVED = """
    DELETE FROM dead_letters
    WHERE archived = 1
      AND dead_at < datetime('now', '-30 days');
"""

SQL_MARK_ARCHIVED = """
    UPDATE dead_letters SET archived = 1
    WHERE archived = 0
      AND dead_at < datetime('now', '-30 days');
"""

# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

MAX_EVENTS_BEFORE_ARCHIVE = 1_000_000
DISK_USAGE_WARN_PERCENT = 80
DISK_USAGE_CRITICAL_PERCENT = 95
TTL_DEFAULT_SECONDS = 86400


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def migrate_to_dead_letter(
    writer: EventBusWriter,
    event_id: int,
    reason: str,
    consumer_id: Optional[str] = None,
) -> None:
    """Move a single event to the dead-letter table.

    Idempotent — uses INSERT OR IGNORE.  The source event's status is
    set to 'dead'.
    """
    conn = writer.conn
    if conn is None:
        return
    # Two-step: first INSERT into dead_letters, then UPDATE events status
    conn.execute(
        """INSERT OR IGNORE INTO dead_letters(
            event_id, source_agent, event_type, payload,
            original_created_at, dead_reason, retry_count, consumer_id
        )
        SELECT
            event_id, source_agent, event_type, payload,
            created_at, ?, retry_count, ?
        FROM events
        WHERE event_id = ?""",
        (reason, consumer_id, event_id),
    )
    conn.execute(
        "UPDATE events SET status = 'dead' WHERE event_id = ?",
        (event_id,),
    )
    conn.commit()


def migrate_expired_events(writer: EventBusWriter, ttl_seconds: int = TTL_DEFAULT_SECONDS) -> int:
    """Batch-migrate all TTL-expired events to dead_letters.  Returns count."""
    conn = writer.conn
    if conn is None:
        return 0
    cur = conn.cursor()
    # Use separate execute calls (sqlite3 execute() does not support multi-statement)
    cur.execute(
        """INSERT OR IGNORE INTO dead_letters(
            event_id, source_agent, event_type, payload,
            original_created_at, dead_reason, retry_count, consumer_id
        )
        SELECT
            event_id, source_agent, event_type, payload,
            created_at, 'TTL_EXPIRED', retry_count, NULL
        FROM events
        WHERE status NOT IN ('processed', 'archived')
          AND created_at < datetime('now', '-' || CAST(? AS TEXT) || ' seconds')
          AND event_id NOT IN (SELECT event_id FROM dead_letters)""",
        (ttl_seconds,),
    )
    cur.execute(
        """UPDATE events SET status = 'dead'
        WHERE status NOT IN ('processed', 'archived')
          AND created_at < datetime('now', '-' || CAST(? AS TEXT) || ' seconds')""",
        (ttl_seconds,),
    )
    conn.commit()
    return cur.rowcount if cur.rowcount > 0 else 0


def archive_overflow(writer: EventBusWriter) -> dict:
    """Check overflow conditions and perform archiving if needed.

    Returns dict with actions taken.
    """
    result = {"events_archived": 0, "dead_cleaned": 0, "vacuumed": False}

    conn = writer.conn
    if conn is None:
        return result

    cur = conn.cursor()

    # --- Step 1: check event count ---
    try:
        row = cur.execute("SELECT COUNT(*) FROM events").fetchone()
        event_count = row[0] if row else 0
    except sqlite3.Error:
        return result

    if event_count > MAX_EVENTS_BEFORE_ARCHIVE:
        logger.warning(
            "Event count %d exceeds %d — triggering archive",
            event_count, MAX_EVENTS_BEFORE_ARCHIVE,
        )
        try:
            cur.execute(
                """INSERT OR IGNORE INTO dead_letters(
                    event_id, source_agent, event_type, payload,
                    original_created_at, dead_reason, retry_count, consumer_id
                )
                SELECT
                    event_id, source_agent, event_type, payload,
                    created_at, 'ARCHIVED_OVERFLOW', retry_count, NULL
                FROM events
                WHERE status = 'processed'
                  AND created_at < datetime('now', '-7 days')"""
            )
            cur.execute(
                "DELETE FROM events WHERE status = 'processed'"
                " AND created_at < datetime('now', '-7 days')"
            )
            conn.commit()
            result["events_archived"] = cur.rowcount if cur.rowcount > 0 else 0
        except sqlite3.Error as exc:
            logger.error("Archive overflow failed: %s", exc)
            conn.rollback()

    # --- Step 2: disk usage check ---
    disk_usage = _get_disk_usage(writer.db_path)
    if disk_usage is not None and disk_usage > DISK_USAGE_WARN_PERCENT:
        logger.warning(
            "Disk usage %.1f%% exceeds %d%% — cleaning dead letters",
            disk_usage, DISK_USAGE_WARN_PERCENT,
        )
        try:
            # Mark old dead letters as archived
            cur.execute(SQL_MARK_ARCHIVED)
            conn.commit()

            # Delete archived dead letters older than 30 days, in batches
            total_cleaned = 0
            while True:
                cur.execute(
                    "DELETE FROM dead_letters "
                    "WHERE archived=1 AND dead_at < datetime('now', '-30 days') "
                    "LIMIT 1000"
                )
                conn.commit()
                batch = cur.rowcount
                if batch == 0:
                    break
                total_cleaned += batch
                time.sleep(0.5)
            result["dead_cleaned"] = total_cleaned

            # VACUUM to reclaim disk — only if dead_cleaned > 0
            # Linus+Guido: VACUUM must NOT be unconditional after each archive.
            # Threshold: only VACUUM if cleaned rows > 0 AND disk > 80%.
            # Production: schedule VACUUM in maintenance window instead.
            if total_cleaned > 0 and (disk_usage is not None and disk_usage > DISK_USAGE_CRITICAL_PERCENT):
                conn.execute("VACUUM")
                conn.commit()
                result["vacuumed"] = True
                logger.info(
                    "VACUUM triggered (cleaned=%d, disk=%.1f%%)",
                    total_cleaned, disk_usage,
                )
            else:
                logger.info(
                    "Skipped VACUUM (cleaned=%d, disk=%s) — threshold not met",
                    total_cleaned, f"{disk_usage:.1f}%" if disk_usage else "N/A",
                )
        except sqlite3.Error as exc:
            logger.error("Dead letter cleanup failed: %s", exc)
            conn.rollback()

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_disk_usage(db_path: str) -> Optional[float]:
    """Return disk usage percentage of the filesystem containing *db_path*."""
    try:
        stat = os.statvfs(os.path.dirname(os.path.abspath(db_path)))
        if stat.f_blocks == 0:
            return None
        return (1.0 - stat.f_bfree / stat.f_blocks) * 100.0
    except OSError:
        return None
