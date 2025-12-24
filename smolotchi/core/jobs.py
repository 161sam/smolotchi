import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class JobRow:
    id: str
    kind: str
    scope: str
    note: str
    status: str
    created_ts: float
    updated_ts: float


class JobStore:
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
                CREATE TABLE IF NOT EXISTS jobs (
                  id TEXT PRIMARY KEY,
                  kind TEXT NOT NULL,
                  scope TEXT NOT NULL,
                  note TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_ts REAL NOT NULL,
                  updated_ts REAL NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_ts)")

    def enqueue(self, job: Dict[str, Any]) -> None:
        now = time.time()
        with self._conn() as con:
            con.execute(
                "INSERT OR REPLACE INTO jobs(id, kind, scope, note, status, created_ts, updated_ts) VALUES(?,?,?,?,?,?,?)",
                (
                    str(job["id"]),
                    str(job["kind"]),
                    str(job["scope"]),
                    str(job.get("note", "")),
                    "queued",
                    float(job.get("created_ts", now)),
                    now,
                ),
            )

    def pop_next(self) -> Optional[JobRow]:
        with self._conn() as con:
            row = con.execute(
                "SELECT id, kind, scope, note, status, created_ts, updated_ts FROM jobs WHERE status='queued' ORDER BY created_ts ASC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            job_id = row[0]
            now = time.time()
            con.execute(
                "UPDATE jobs SET status='running', updated_ts=? WHERE id=?",
                (now, job_id),
            )
            return JobRow(*row[:5], float(row[5]), now)

    def mark_done(self, job_id: str) -> None:
        with self._conn() as con:
            con.execute(
                "UPDATE jobs SET status='done', updated_ts=? WHERE id=?",
                (time.time(), job_id),
            )

    def mark_failed(self, job_id: str, note: str = "") -> None:
        with self._conn() as con:
            cur = con.execute("SELECT note FROM jobs WHERE id=?", (job_id,)).fetchone()
            base = (cur[0] if cur else "") or ""
            merged = (base + "\n" + note).strip()
            con.execute(
                "UPDATE jobs SET status='failed', note=?, updated_ts=? WHERE id=?",
                (merged, time.time(), job_id),
            )

    def list(self, limit: int = 50, status: Optional[str] = None) -> List[JobRow]:
        q = "SELECT id, kind, scope, note, status, created_ts, updated_ts FROM jobs "
        params: List[Any] = []
        if status:
            q += "WHERE status=? "
            params.append(status)
        q += "ORDER BY created_ts DESC LIMIT ?"
        params.append(limit)

        out: List[JobRow] = []
        with self._conn() as con:
            for row in con.execute(q, params):
                out.append(
                    JobRow(
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        row[4],
                        float(row[5]),
                        float(row[6]),
                    )
                )
        return out
