from __future__ import annotations

import datetime as dt
import logging
import sqlite3
from pathlib import Path
from typing import Callable, Iterable

logger = logging.getLogger("smolotchi.core.migrations")


Migration = Callable[[sqlite3.Connection], None]


def _utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _schema_version_table_exists(con: sqlite3.Connection) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    return row is not None


def get_current_schema_version(con: sqlite3.Connection) -> int:
    if not _schema_version_table_exists(con):
        return 0
    row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
    if not row or row[0] is None:
        return 0
    return int(row[0])


def _migration_001(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
          version INTEGER NOT NULL,
          applied_at TEXT NOT NULL,
          app_version TEXT
        )
        """
    )


MIGRATIONS: Iterable[tuple[int, Migration]] = [
    (1, _migration_001),
]


def apply_migrations(db_path: str, app_version: str | None = None) -> None:
    Path(Path(db_path).parent).mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        current_version = get_current_schema_version(con)
        for version, migration in MIGRATIONS:
            if version <= current_version:
                continue
            logger.info("Applying DB migration %s", version)
            with con:
                migration(con)
                con.execute(
                    "INSERT INTO schema_version(version, applied_at, app_version) VALUES(?,?,?)",
                    (version, _utc_now_iso(), app_version),
                )
            current_version = version
        logger.info("DB schema at version %s", current_version)
