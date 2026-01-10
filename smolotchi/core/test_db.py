import sqlite3
import tempfile
import unittest

from smolotchi.core.db import bootstrap_db, inspect_db


class DatabaseBootstrapTest(unittest.TestCase):
    def test_bootstrap_creates_schema_and_wal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            bootstrap_db(db_path)

            with sqlite3.connect(db_path) as con:
                row = con.execute("SELECT MAX(version) FROM schema_version").fetchone()
                self.assertIsNotNone(row)
                self.assertEqual(row[0], 1)
                cols = {r[1] for r in con.execute("PRAGMA table_info(schema_version)")}
                self.assertIn("applied_ts", cols)
                self.assertIn("note", cols)
                mode = con.execute("PRAGMA journal_mode").fetchone()
                self.assertIsNotNone(mode)
                self.assertEqual(mode[0], "wal")

    def test_inspect_db_reports_schema_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = f"{tmpdir}/events.db"
            bootstrap_db(db_path)

            info = inspect_db(db_path)
            self.assertEqual(info["schema_version"], 1)
            self.assertEqual(info["journal_mode"], "wal")


if __name__ == "__main__":
    unittest.main()
