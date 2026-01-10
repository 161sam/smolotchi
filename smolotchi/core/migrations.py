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


def _schema_version_table_exists(con: sqlite3.Connection) -> bool:
    row = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_version'"
    ).fetchone()
    return row is not None


def _schema_version_columns(con: sqlite3.Connection, table: str) -> list[str]:
    try:
        rows = con.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.OperationalError:
        return []
    return [str(row[1]) for row in rows]


def _schema_version_table_valid(con: sqlite3.Connection) -> bool:
    if not _schema_version_table_exists(con):
        return False
    columns = set(_schema_version_columns(con, "schema_version"))
    return {"version", "applied_ts", "note"}.issubset(columns)


def _parse_applied_ts(value: object | None) -> float:
    if value is None:
        return time.time()
    if isinstance(value, (int, float)):
        return float(value)
    raw = str(value)
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        parsed = dt.datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.timestamp()
    except Exception:
        return time.time()


def _ensure_schema_version_table(con: sqlite3.Connection) -> None:
    if _schema_version_table_valid(con):
        return
    legacy_columns = _schema_version_columns(con, "schema_version")
    legacy_rows: list[tuple[int, float, str | None]] = []
    if legacy_columns:
        select_columns = []
        if "version" in legacy_columns:
            select_columns.append("version")
        if "applied_ts" in legacy_columns:
            select_columns.append("applied_ts")
        elif "applied_at" in legacy_columns:
            select_columns.append("applied_at")
        if "note" in legacy_columns:
            select_columns.append("note")
        elif "app_version" in legacy_columns:
            select_columns.append("app_version")
        if select_columns:
            rows = con.execute(
                f"SELECT {', '.join(select_columns)} FROM schema_version"
            ).fetchall()
            for row in rows:
                row_map = dict(zip(select_columns, row))
                version = int(row_map.get("version") or 0)
                if "applied_ts" in row_map:
                    applied_ts = _parse_applied_ts(row_map.get("applied_ts"))
                else:
                    applied_ts = _parse_applied_ts(row_map.get("applied_at"))
                note = row_map.get("note") or row_map.get("app_version")
                legacy_rows.append((version, applied_ts, str(note) if note else None))
        con.execute("ALTER TABLE schema_version RENAME TO schema_version_legacy")

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
          version INTEGER NOT NULL,
          applied_ts REAL NOT NULL,
          note TEXT
        )
        """
    )
    if legacy_rows:
        con.executemany(
            "INSERT INTO schema_version(version, applied_ts, note) VALUES(?,?,?)",
            legacy_rows,
        )
    if legacy_columns:
        con.execute("DROP TABLE IF EXISTS schema_version_legacy")


def get_current_schema_version(con: sqlite3.Connection) -> int:
    if not _schema_version_table_exists(con):
        return 0
    row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
    if not row or row[0] is None:
        return 0
    return int(row[0])


def _migration_001(con: sqlite3.Connection) -> None:
    _ensure_schema_version_table(con)


MIGRATIONS: Iterable[tuple[int, Migration]] = [
    (1, _migration_001),
]


def _run_migrations(
    con: sqlite3.Connection, app_version: str | None, *, dry_run: bool = False
) -> dict[str, object]:
    if not dry_run:
        _ensure_schema_version_table(con)
    current_version = get_current_schema_version(con)
    latest_version = max((version for version, _ in MIGRATIONS), default=0)
    pending_versions: list[int] = []
    applied_versions: list[int] = []
    for version, migration in MIGRATIONS:
        if version <= current_version:
            continue
        if dry_run:
            pending_versions.append(version)
            continue
        logger.info("Applying DB migration %s", version)
        with con:
            migration(con)
            con.execute(
                "INSERT INTO schema_version(version, applied_ts, note) VALUES(?,?,?)",
                (version, time.time(), app_version),
            )
        current_version = version
        applied_versions.append(version)
    logger.info("DB schema at version %s", current_version)
    return {
        "current_version": current_version,
        "latest_version": latest_version,
        "pending": pending_versions,
        "applied": applied_versions,
    }


def apply_migrations_on_connection(
    con: sqlite3.Connection, app_version: str | None = None
) -> int:
    _run_migrations(con, app_version)
    return get_current_schema_version(con)


def plan_migrations_on_connection(con: sqlite3.Connection) -> dict[str, object]:
    return _run_migrations(con, None, dry_run=True)


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
