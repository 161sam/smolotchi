from __future__ import annotations

import sqlite3

DEFAULT_BUSY_TIMEOUT_MS = 5000
DEFAULT_TIMEOUT_S = 5.0


def configure_connection(
    con: sqlite3.Connection, *, busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS
) -> None:
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute(f"PRAGMA busy_timeout={int(busy_timeout_ms)}")


def connect(
    db_path: str,
    *,
    timeout: float = DEFAULT_TIMEOUT_S,
    busy_timeout_ms: int = DEFAULT_BUSY_TIMEOUT_MS,
) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=timeout)
    configure_connection(con, busy_timeout_ms=busy_timeout_ms)
    return con
