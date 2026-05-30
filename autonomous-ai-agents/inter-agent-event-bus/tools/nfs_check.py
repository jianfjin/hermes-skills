"""nfs_check — Filesystem type check for WAL-mode safety.

SQLite WAL mode silently corrupts data on network / fuse filesystems.
This module must run at init, BEFORE any database connection is opened.

Linus: "WAL模式在网络文件系统上直接宕机——静默数据损坏"
"""

from __future__ import annotations

import logging
import os
import subprocess

logger = logging.getLogger(__name__)


class FilesystemNotSupportedError(Exception):
    """Raised when the database directory is on an unsafe filesystem.

    Dijkstra: \"sys.exit(1) from a library module is not a library —
    it is a time bomb. Raise an exception; let the caller decide to exit.\"
    """
    def __init__(self, db_dir: str, fs_type: str):
        self.db_dir = db_dir
        self.fs_type = fs_type
        super().__init__(
            f"Database directory '{db_dir}' is on '{fs_type}' filesystem.\n"
            "SQLite WAL mode does NOT support network / fuse filesystems.\n"
            "Data corruption is guaranteed if WAL runs on NFS/CIFS/FUSE.\n"
            "Solution: Use local disk or set journal_mode=DELETE."
        )


# Filesystem types known to break WAL-mode journaling.
# stat -f -c %T returns the type name (lowercase on Linux).
BLOCKED_FS_TYPES = {
    "nfs",
    "nfs4",
    "cifs",
    "smb2",
    "smb3",
    "fuse",
    "fuse.sshfs",
    "fuse.glusterfs",
}


def check_filesystem_type(db_path: str) -> None:
    """Verify *db_path* resides on a WAL-safe filesystem.

    Calls ``stat -f -c %T``.  If the filesystem type is in the blocked
    set, raises ``FilesystemNotSupportedError``. Caller decides how to handle.
    (Dijkstra: library modules must not sys.exit.)

    Non-fatal warnings are logged when ``stat`` is missing or times out.
    """
    db_dir = os.path.dirname(os.path.abspath(db_path))

    # Ensure the directory exists for stat to work
    os.makedirs(db_dir, exist_ok=True)

    try:
        result = subprocess.run(
            ["stat", "-f", "-c", "%T", db_dir],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        logger.warning("'stat' command not found — skipping NFS check")
        return
    except subprocess.TimeoutExpired:
        logger.warning("stat command timed out — skipping NFS check")
        return
    except Exception as exc:
        logger.warning("NFS check failed (%s) — skipping", exc)
        return

    fs_type = result.stdout.strip().lower()
    if not fs_type:
        logger.warning("stat returned empty filesystem type — skipping NFS check")
        return

    if fs_type in BLOCKED_FS_TYPES:
        raise FilesystemNotSupportedError(db_dir, fs_type)

    logger.info("Filesystem type check passed: %s", fs_type)
