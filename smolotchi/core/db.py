from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from smolotchi.core.migrations import apply_migrations_on_connection, get_current_schema_version
from smolotchi.core.sqlite import (
    DEFAULT_BUSY_TIMEOUT_MS,
    DEFAULT_TIMEOUT_S,
    connect,
)


def bootstrap_db(
    db_path: str,
    *,
    app_version: str | None = None,
    timeout: float = DEFAULT_TIMEOUT_S,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with connect(str(path), timeout=timeout, busy_timeout_ms=busy_timeout_ms) as con:
        apply_migrations_on_connection(con, app_version)
        journal_mode = con.execute("PRAGMA journal_mode").fetchone()
        busy_timeout = con.execute("PRAGMA busy_timeout").fetchone()
        schema_version = get_current_schema_version(con)
    return {
        "db_path": str(path),
        "journal_mode": str(journal_mode[0]) if journal_mode else "unknown",
        "schema_version": schema_version,
        "busy_timeout_ms": int(busy_timeout[0]) if busy_timeout else 0,
    }


def inspect_db(db_path: str) -> dict[str, Any]:
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        return {
            "db_path": str(path),
            "journal_mode": "missing",
            "schema_version": 0,
            "busy_timeout_ms": 0,
        }
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    except sqlite3.OperationalError:
        con = sqlite3.connect(str(path))
    with con:
        journal_mode = con.execute("PRAGMA journal_mode").fetchone()
        busy_timeout = con.execute("PRAGMA busy_timeout").fetchone()
        schema_version = get_current_schema_version(con)
    return {
        "db_path": str(path),
        "journal_mode": str(journal_mode[0]) if journal_mode else "unknown",
        "schema_version": schema_version,
        "busy_timeout_ms": int(busy_timeout[0]) if busy_timeout else 0,
    }
