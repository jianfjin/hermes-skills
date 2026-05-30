#!/usr/bin/env python3
"""migrate_schema_v2 — Standalone schema migration runner.

Usage::

    python migrate_schema_v2.py --db-path /path/to/event_bus.db

Exits 0 on success, 1 on failure.
"""

from __future__ import annotations

import argparse
import os
import sys

# Ensure tools/ is on path so we can import from there
_TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
if _TOOLS_DIR not in sys.path:
    sys.path.insert(0, _TOOLS_DIR)

from connection import EventBusWriter
from event_schema_v2 import SCHEMA_VERSION, run_migrations
from nfs_check import check_filesystem_type


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Migrate event-bus database to schema v{SCHEMA_VERSION}"
    )
    parser.add_argument(
        "--db-path",
        required=True,
        help="Path to the event bus SQLite database",
    )
    args = parser.parse_args()

    db_path = os.path.abspath(args.db_path)

    # NFS check BEFORE opening any connection
    check_filesystem_type(db_path)

    # Create writer and connect
    writer = EventBusWriter(db_path)
    writer.connect()

    try:
        run_migrations(writer)
    except RuntimeError as exc:
        print(f"ERROR: Migration failed: {exc}", file=sys.stderr)
        return 1
    finally:
        writer.close()

    print(f"Schema migration to v{SCHEMA_VERSION} complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
