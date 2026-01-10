from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from smolotchi.core.paths import resolve_db_path
from smolotchi.core.migrations import apply_migrations


@dataclass
class JobRow:
    id: str
    kind: str
    scope: str
    note: str
    meta: Dict[str, Any]
    status: str
    created_ts: float
    updated_ts: float


class JobStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or resolve_db_path()
        Path(Path(self.db_path).parent).mkdir(parents=True, exist_ok=True)
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
                  meta TEXT NOT NULL,
                  status TEXT NOT NULL,
                  created_ts REAL NOT NULL,
                  updated_ts REAL NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_ts)")
            cols = {row[1] for row in con.execute("PRAGMA table_info(jobs)").fetchall()}
            if "meta" not in cols:
                con.execute("ALTER TABLE jobs ADD COLUMN meta TEXT NOT NULL DEFAULT '{}'")
        apply_migrations(self.db_path)

    def enqueue(self, job: Dict[str, Any]) -> None:
        now = time.time()
        meta = job.get("meta") or {}
        meta_json = json.dumps(meta, ensure_ascii=False)
        with self._conn() as con:
            con.execute(
                "INSERT OR REPLACE INTO jobs(id, kind, scope, note, meta, status, created_ts, updated_ts) VALUES(?,?,?,?,?,?,?,?)",
                (
                    str(job["id"]),
                    str(job["kind"]),
                    str(job["scope"]),
                    str(job.get("note", "")),
                    meta_json,
                    "queued",
                    float(job.get("created_ts", now)),
                    now,
                ),
            )

    def get(self, job_id: str) -> Optional[JobRow]:
        with self._conn() as con:
            row = con.execute(
                "SELECT id, kind, scope, note, meta, status, created_ts, updated_ts FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
            if not row:
                return None
            return JobRow(
                row[0],
                row[1],
                row[2],
                row[3],
                json.loads(row[4] or "{}"),
                row[5],
                float(row[6]),
                float(row[7]),
            )

    def pop_next(self) -> Optional[JobRow]:
        return self.pop_next_filtered()

    def pop_next_filtered(
        self,
        *,
        include_prefixes: Optional[List[str]] = None,
        exclude_prefixes: Optional[List[str]] = None,
        include_kinds: Optional[List[str]] = None,
        exclude_kinds: Optional[List[str]] = None,
    ) -> Optional[JobRow]:
        include_prefixes = include_prefixes or []
        exclude_prefixes = exclude_prefixes or []
        include_kinds = include_kinds or []
        exclude_kinds = exclude_kinds or []

        query = (
            "SELECT id, kind, scope, note, meta, status, created_ts, updated_ts "
            "FROM jobs WHERE status='queued'"
        )
        params: List[Any] = []

        allow_clauses: List[str] = []
        if include_kinds:
            allow_clauses.append(
                "kind IN (" + ",".join("?" for _ in include_kinds) + ")"
            )
            params.extend(include_kinds)
        if include_prefixes:
            allow_clauses.append(
                " OR ".join("kind LIKE ?" for _ in include_prefixes)
            )
            params.extend([f"{prefix}%" for prefix in include_prefixes])
        if allow_clauses:
            query += " AND (" + " OR ".join(allow_clauses) + ")"

        if exclude_kinds:
            query += " AND kind NOT IN (" + ",".join("?" for _ in exclude_kinds) + ")"
            params.extend(exclude_kinds)
        if exclude_prefixes:
            query += " AND " + " AND ".join("kind NOT LIKE ?" for _ in exclude_prefixes)
            params.extend([f"{prefix}%" for prefix in exclude_prefixes])

        query += " ORDER BY created_ts ASC LIMIT 1"

        with self._conn() as con:
            row = con.execute(query, params).fetchone()
            if not row:
                return None
            job_id = row[0]
            now = time.time()
            con.execute(
                "UPDATE jobs SET status='running', updated_ts=? WHERE id=?",
                (now, job_id),
            )
            meta = json.loads(row[4] or "{}")
            return JobRow(
                row[0],
                row[1],
                row[2],
                row[3],
                meta,
                row[5],
                float(row[6]),
                now,
            )

    def mark_running(self, job_id: str) -> None:
        with self._conn() as con:
            con.execute(
                "UPDATE jobs SET status='running', updated_ts=? WHERE id=?",
                (time.time(), job_id),
            )

    def update_note(self, job_id: str, note: str) -> None:
        with self._conn() as con:
            con.execute(
                "UPDATE jobs SET note=?, updated_ts=? WHERE id=?",
                (note, time.time(), job_id),
            )

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

    def mark_blocked(self, job_id: str, note: str = "blocked") -> None:
        with self._conn() as con:
            cur = con.execute("SELECT note FROM jobs WHERE id=?", (job_id,)).fetchone()
            base = (cur[0] if cur else "") or ""
            merged = (base + "\n" + note).strip()
            con.execute(
                "UPDATE jobs SET status='blocked', note=?, updated_ts=? WHERE id=?",
                (merged, time.time(), job_id),
            )

    def mark_cancelled(self, job_id: str, note: str = "cancelled") -> None:
        with self._conn() as con:
            cur = con.execute("SELECT note FROM jobs WHERE id=?", (job_id,)).fetchone()
            base = (cur[0] if cur else "") or ""
            merged = (base + "\n" + note).strip()
            con.execute(
                "UPDATE jobs SET status='cancelled', note=?, updated_ts=? WHERE id=?",
                (merged, time.time(), job_id),
            )

    def mark_queued(self, job_id: str, note: str = "") -> None:
        with self._conn() as con:
            if note:
                cur = con.execute("SELECT note FROM jobs WHERE id=?", (job_id,)).fetchone()
                base = (cur[0] if cur else "") or ""
                merged = (base + "\n" + note).strip()
                con.execute(
                    "UPDATE jobs SET status='queued', note=?, updated_ts=? WHERE id=?",
                    (merged, time.time(), job_id),
                )
            else:
                con.execute(
                    "UPDATE jobs SET status='queued', updated_ts=? WHERE id=?",
                    (time.time(), job_id),
                )

    def list(self, limit: int = 50, status: Optional[str] = None) -> List[JobRow]:
        q = "SELECT id, kind, scope, note, meta, status, created_ts, updated_ts FROM jobs "
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
                        json.loads(row[4] or "{}"),
                        row[5],
                        float(row[6]),
                        float(row[7]),
                    )
                )
        return out

    def list_recent(self, limit: int = 10) -> List[JobRow]:
        return self.list(limit=limit, status=None)

    def list_stuck_running(
        self, older_than_seconds: int = 180, limit: int = 50
    ) -> List[JobRow]:
        cutoff = time.time() - older_than_seconds
        out: List[JobRow] = []
        with self._conn() as con:
            for row in con.execute(
                "SELECT id, kind, scope, note, meta, status, created_ts, updated_ts "
                "FROM jobs WHERE status='running' AND updated_ts < ? "
                "ORDER BY updated_ts ASC LIMIT ?",
                (cutoff, limit),
            ):
                out.append(
                    JobRow(
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        json.loads(row[4] or "{}"),
                        row[5],
                        float(row[6]),
                        float(row[7]),
                    )
                )
        return out

    def _stuck_running_ids(
        self, older_than_seconds: int = 180, limit: int = 50
    ) -> List[str]:
        cutoff = time.time() - older_than_seconds
        with self._conn() as con:
            rows = con.execute(
                "SELECT id FROM jobs WHERE status='running' AND updated_ts < ? "
                "ORDER BY updated_ts ASC LIMIT ?",
                (cutoff, limit),
            ).fetchall()
        return [str(row[0]) for row in rows]

    def reset_stuck(self, older_than_seconds: int = 180, limit: int = 50) -> int:
        ids = self._stuck_running_ids(
            older_than_seconds=older_than_seconds, limit=limit
        )
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self._conn() as con:
            cur = con.execute(
                f"UPDATE jobs SET status='queued', updated_ts=? "
                f"WHERE id IN ({placeholders})",
                (time.time(), *ids),
            )
            return cur.rowcount

    def fail_stuck(
        self,
        older_than_seconds: int = 180,
        limit: int = 50,
        note: str = "watchdog: stuck",
    ) -> int:
        ids = self._stuck_running_ids(
            older_than_seconds=older_than_seconds, limit=limit
        )
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with self._conn() as con:
            cur = con.execute(
                f"UPDATE jobs SET status='failed', note=trim(note || '\n' || ?), updated_ts=? "
                f"WHERE id IN ({placeholders})",
                (note, time.time(), *ids),
            )
            return cur.rowcount

    def cancel(self, job_id: str) -> bool:
        """
        Cancel queued or running jobs -> mark cancelled.
        """
        with self._conn() as con:
            row = con.execute(
                "SELECT status FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            if not row:
                return False
            if row[0] not in {"queued", "running", "blocked"}:
                return False
            con.execute(
                "UPDATE jobs SET status='cancelled', note=trim(note || '\n' || ?), updated_ts=? WHERE id=?",
                ("cancelled", time.time(), job_id),
            )
            return True

    def reset_running(self, job_id: str) -> bool:
        """
        Reset stuck running job -> queued.
        """
        with self._conn() as con:
            row = con.execute(
                "SELECT status FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            if not row:
                return False
            if row[0] != "running":
                return False
            con.execute(
                "UPDATE jobs SET status='queued', updated_ts=? WHERE id=?",
                (time.time(), job_id),
            )
            return True

    def fail(self, job_id: str, note: str = "watchdog: stuck") -> bool:
        """
        Fail running job -> failed.
        """
        with self._conn() as con:
            row = con.execute(
                "SELECT status FROM jobs WHERE id=?", (job_id,)
            ).fetchone()
            if not row:
                return False
            if row[0] != "running":
                return False
            con.execute(
                "UPDATE jobs SET status='failed', note=trim(note || '\n' || ?), updated_ts=? WHERE id=?",
                (note, time.time(), job_id),
            )
            return True

    def delete(self, job_id: str) -> bool:
        with self._conn() as con:
            cur = con.execute("DELETE FROM jobs WHERE id=?", (job_id,))
            return cur.rowcount > 0

    def prune(self, keep_last: int = 1000, done_failed_older_than_days: int = 14) -> int:
        """
        Prune old done/failed jobs + cap table to keep_last newest rows.
        Returns number of deleted rows.
        """
        deleted = 0
        cutoff = time.time() - (done_failed_older_than_days * 86400)

        with self._conn() as con:
            cur = con.execute(
                "DELETE FROM jobs WHERE (status='done' OR status='failed') AND updated_ts < ?",
                (cutoff,),
            )
            deleted += cur.rowcount

            cur = con.execute(
                "DELETE FROM jobs WHERE id IN (SELECT id FROM jobs ORDER BY created_ts DESC LIMIT -1 OFFSET ?)",
                (keep_last,),
            )
            deleted += cur.rowcount

        return deleted
