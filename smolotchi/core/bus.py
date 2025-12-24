import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


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

    def __init__(self, db_path: str = "/var/lib/smolotchi/events.db"):
        self.db_path = db_path
        Path(Path(db_path).parent).mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

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
