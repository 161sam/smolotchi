from __future__ import annotations

import datetime as dt
import logging
import sqlite3
import time
from pathlib import Path
from typing import Callable, Iterable

from smolotchi.core.sqlite import connect
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


def _run_migrations(con: sqlite3.Connection, app_version: str | None) -> None:
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


def apply_migrations_on_connection(
    con: sqlite3.Connection, app_version: str | None = None
) -> int:
    _run_migrations(con, app_version)
    return get_current_schema_version(con)


def _is_busy_error(exc: sqlite3.OperationalError) -> bool:
    message = str(exc).lower()
    return "locked" in message or "busy" in message


def apply_migrations(
    db_path: str,
    app_version: str | None = None,
    *,
    timeout: float = 30.0,
    busy_timeout_ms: int = 5000,
    max_retries: int = 5,
    retry_backoff_s: float = 0.5,
) -> None:
    Path(Path(db_path).parent).mkdir(parents=True, exist_ok=True)
    attempt = 0
    while True:
        try:
            with connect(db_path, timeout=timeout, busy_timeout_ms=busy_timeout_ms) as con:
                _run_migrations(con, app_version)
            return
        except sqlite3.OperationalError as exc:
            if _is_busy_error(exc) and attempt < max_retries:
                sleep_for = retry_backoff_s * (2**attempt)
                logger.warning(
                    "DB busy/locked during migrations, retrying in %.2fs", sleep_for
                )
                time.sleep(sleep_for)
                attempt += 1
                continue
            raise
