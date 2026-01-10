from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from smolotchi.core.paths import resolve_db_path
from smolotchi.core.sqlite import connect


@dataclass
class Event:
    ts: float
    topic: str
    payload: Dict[str, Any]


class SQLiteBus:
    """
    Minimaler Event-Bus: append-only Events in SQLite.
    Reicht für v0.0.1 + lässt sich später durch Redis/MQTT ersetzen.
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or resolve_db_path()
        Path(Path(self.db_path).parent).mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return connect(self.db_path)

    def _init_db(self) -> None:
        with self._conn() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ts REAL NOT NULL,
                  topic TEXT NOT NULL,
                  payload TEXT NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic)")

    @property
    def db_path_value(self) -> str:
        return self.db_path

    def publish(self, topic: str, payload: Dict[str, Any]) -> None:
        evt = Event(ts=time.time(), topic=topic, payload=payload)
        with self._conn() as con:
            con.execute(
                "INSERT INTO events(ts, topic, payload) VALUES(?,?,?)",
                (evt.ts, evt.topic, json.dumps(evt.payload, ensure_ascii=False)),
            )

    def tail(self, limit: int = 50, topic_prefix: Optional[str] = None) -> List[Event]:
        q = "SELECT ts, topic, payload FROM events "
        params: List[Any] = []
        if topic_prefix:
            q += "WHERE topic LIKE ? "
            params.append(f"{topic_prefix}%")
        q += "ORDER BY id DESC LIMIT ?"
        params.append(limit)

        out: List[Event] = []
        with self._conn() as con:
            for ts, topic, payload in con.execute(q, params):
                out.append(Event(ts=float(ts), topic=str(topic), payload=json.loads(payload)))
        return out

    def prune(
        self, keep_last: int = 5000, older_than_days: int = 30, vacuum: bool = False
    ) -> int:
        """
        Keep last N events AND delete events older than days.
        Returns number deleted.
        """
        deleted = 0
        cutoff = time.time() - (older_than_days * 86400)

        with self._conn() as con:
            cur = con.execute("DELETE FROM events WHERE ts < ?", (cutoff,))
            deleted += cur.rowcount

            cur = con.execute(
                "DELETE FROM events WHERE id IN (SELECT id FROM events ORDER BY id DESC LIMIT -1 OFFSET ?)",
                (keep_last,),
            )
            deleted += cur.rowcount

            if vacuum:
                con.execute("VACUUM")

        return deleted
