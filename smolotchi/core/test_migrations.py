import sqlite3
import tempfile
import threading
import time
import unittest

from smolotchi.core.migrations import apply_migrations


class MigrationRunnerTest(unittest.TestCase):
    def test_empty_db_migrates_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            apply_migrations(db_path)

            with sqlite3.connect(db_path) as con:
                row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)
                cols = {r[1] for r in con.execute("PRAGMA table_info(schema_version)")}
                self.assertIn("applied_ts", cols)
                self.assertIn("note", cols)

    def test_db_without_schema_version_is_upgraded(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            with sqlite3.connect(db_path) as con:
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
            apply_migrations(db_path)

            with sqlite3.connect(db_path) as con:
                row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)
                table = con.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='events'"
                ).fetchone()
                self.assertIsNotNone(table)

    def test_legacy_schema_version_table_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            with sqlite3.connect(db_path) as con:
                con.execute(
                    """
                    CREATE TABLE schema_version (
                      version INTEGER NOT NULL,
                      applied_at TEXT NOT NULL,
                      app_version TEXT
                    )
                    """
                )
                con.execute(
                    "INSERT INTO schema_version(version, applied_at, app_version) VALUES(?,?,?)",
                    (1, "2024-01-01T00:00:00+00:00", "legacy"),
                )
            apply_migrations(db_path)

            with sqlite3.connect(db_path) as con:
                cols = {r[1] for r in con.execute("PRAGMA table_info(schema_version)")}
                self.assertIn("applied_ts", cols)
                self.assertIn("note", cols)
                row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)

    def test_wal_mode_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            apply_migrations(db_path)

            with sqlite3.connect(db_path) as con:
                mode = con.execute("PRAGMA journal_mode").fetchone()
                self.assertIsNotNone(mode)
                self.assertEqual(mode[0], "wal")

    def test_apply_migrations_retries_on_busy_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            lock_con = sqlite3.connect(db_path)
            lock_con.execute("BEGIN IMMEDIATE")

            errors: list[Exception] = []

            def run_migrations() -> None:
                try:
                    apply_migrations(
                        db_path,
                        timeout=0.1,
                        busy_timeout_ms=100,
                        max_retries=5,
                        retry_backoff_s=0.1,
                    )
                except Exception as exc:  # pragma: no cover - diagnostic
                    errors.append(exc)

            thread = threading.Thread(target=run_migrations)
            thread.start()
            time.sleep(0.2)
            lock_con.commit()
            lock_con.close()
            thread.join(timeout=5)

            self.assertFalse(thread.is_alive())
            self.assertFalse(errors)
            with sqlite3.connect(db_path) as con:
                row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
                self.assertIsNotNone(row)


if __name__ == "__main__":
    unittest.main()
