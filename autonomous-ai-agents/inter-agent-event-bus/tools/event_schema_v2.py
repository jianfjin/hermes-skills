"""event_schema_v2 — Event Schema v2 definition and migrations.

Schema version 2 introduces:
  - events            — main event table (INTEGER PK, status lifecycle)
  - consumer_cursors  — per-consumer read position tracking
  - dead_letters      — failed/expired event archive

Linus: "回答'event长什么样'这个问题，一半问题自动解决。"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from connection import EventBusWriter

logger = logging.getLogger(__name__)

MAX_TTL_SECONDS = 86400  # 24 hours — symbolic constant (Dijkstra: no magic numbers)

# ---------------------------------------------------------------------------
# Table DDL (idempotent — IF NOT EXISTS)
# ---------------------------------------------------------------------------

DDL_EVENTS = """
CREATE TABLE IF NOT EXISTS events (
    event_id     INTEGER PRIMARY KEY,
    source_agent TEXT    NOT NULL,
    event_type   TEXT    NOT NULL,
    payload      TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending','processing','processed','dead','archived')),
    created_at   TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    processed_at TEXT,
    retry_count  INTEGER NOT NULL DEFAULT 0,
    max_retries  INTEGER NOT NULL DEFAULT 3,
    error_message TEXT,
    ttl_seconds  INTEGER DEFAULT MAX_TTL_SECONDS
);
"""

DDL_CONSUMER_CURSORS = """
CREATE TABLE IF NOT EXISTS consumer_cursors (
    consumer_id   TEXT PRIMARY KEY,
    last_event_id INTEGER NOT NULL DEFAULT 0,
    updated_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
"""

DDL_DEAD_LETTERS = """
CREATE TABLE IF NOT EXISTS dead_letters (
    event_id            INTEGER PRIMARY KEY,
    source_agent        TEXT    NOT NULL,
    event_type          TEXT    NOT NULL,
    payload             TEXT    NOT NULL,
    original_created_at TEXT    NOT NULL,
    dead_at             TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    dead_reason         TEXT    NOT NULL,
    retry_count         INTEGER NOT NULL,
    consumer_id         TEXT,
    archived            INTEGER NOT NULL DEFAULT 0
);
"""

DDL_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_events_status           ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_created           ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_dead_letters_archived    ON dead_letters(archived);
"""

# ---------------------------------------------------------------------------
# Migration definitions
# ---------------------------------------------------------------------------

MIGRATIONS = {
    1: f"""
        -- v1 → v2: Initial Event Schema v2 deployment
        {DDL_EVENTS}
        {DDL_CONSUMER_CURSORS}
        {DDL_DEAD_LETTERS}
        {DDL_INDEXES}
    """,
}

SCHEMA_VERSION = max(MIGRATIONS.keys())  # highest available migration (#)
# Migration runner
# ---------------------------------------------------------------------------


def run_migrations(writer: "EventBusWriter") -> None:
    """Apply pending schema migrations on the writer connection.

    Idempotent — safe to call at every startup.
    All migrations run in a single transaction; rollback on failure.
    """
    conn = writer.conn
    if conn is None:
        writer.connect()
        conn = writer.conn
        if conn is None:
            raise RuntimeError("Writer connection is None after connect() — abort")

    cur = conn.cursor()

    # Ensure schema_version table exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version    INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
    """)

    # Determine current version
    row = cur.execute("SELECT MAX(version) FROM schema_version").fetchone()
    current = row[0] if row and row[0] is not None else 0

    if current >= SCHEMA_VERSION:
        logger.debug("Schema is up-to-date (v%d)", current)
        return

    logger.info("Running migrations from v%d to v%d", current, SCHEMA_VERSION)

    for ver in sorted(MIGRATIONS.keys()):
        if ver <= current:
            continue
        try:
            cur.executescript(MIGRATIONS[ver])
            cur.execute(
                "INSERT INTO schema_version (version, applied_at) "
                "VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                (ver,),
            )
            conn.commit()
            logger.info("Migration v%d applied successfully", ver)
        except Exception as exc:
            conn.rollback()
            logger.critical("Migration v%d failed: %s", ver, exc)
            raise RuntimeError(f"Migration v{ver} failed: {exc}") from exc

    logger.info("All migrations complete. Schema at v%d", SCHEMA_VERSION)
