import sqlite3
import tempfile
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


if __name__ == "__main__":
    unittest.main()
