from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sqlite3

import smolotchi.cli as cli
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.locks import LOCK_SUFFIX, META_SUFFIX, write_lock


def test_db_migrate_applies_schema_version(tmp_path, capsys) -> None:
    db_path = tmp_path / "events.db"
    with sqlite3.connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts REAL NOT NULL,
              topic TEXT NOT NULL,
              payload TEXT NOT NULL
            )
            """
        )

    exit_code = cli.main(["--db", str(db_path), "db", "migrate", "--format", "json"])
    assert exit_code == cli.EX_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["current_version"] == 1

    with sqlite3.connect(db_path) as con:
        cols = {row[1] for row in con.execute("PRAGMA table_info(schema_version)")}
        assert "applied_ts" in cols
        assert "note" in cols


def test_db_migrate_dry_run_reports_pending(tmp_path, capsys) -> None:
    db_path = tmp_path / "events.db"
    exit_code = cli.main(
        ["--db", str(db_path), "db", "migrate", "--dry-run", "--format", "json"]
    )
    assert exit_code == cli.EX_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["pending"] == [1]
    assert payload["applied"] == []


def test_artifacts_verify_reports_failures(tmp_path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    store = ArtifactStore(str(artifact_root))
    meta = store.put_text("note", "hello", "payload")
    Path(meta.path).write_bytes(b"tampered")

    exit_code = cli.main(
        [
            "--artifact-root",
            str(artifact_root),
            "artifacts",
            "verify",
            "--kind",
            "note",
            "--format",
            "json",
        ]
    )
    assert exit_code == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 1
    assert payload["failed"][0]["id"] == meta.id


def test_locks_check_and_clean(tmp_path, capsys) -> None:
    lock_root = tmp_path / "locks"
    lock_path = lock_root / f"worker{LOCK_SUFFIX}"
    meta = write_lock(lock_path, purpose="test")
    meta["created_at"] = (
        datetime.now(timezone.utc) - timedelta(hours=2)
    ).replace(microsecond=0).isoformat()
    Path(lock_path.with_suffix(META_SUFFIX)).write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    exit_code = cli.main(
        [
            "locks",
            "check",
            "--lock-root",
            str(lock_root),
            "--ttl-min",
            "1",
            "--format",
            "json",
        ]
    )
    assert exit_code == cli.EX_VALIDATION
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["stale_ttl"] == 1

    exit_code = cli.main(
        [
            "locks",
            "clean",
            "--lock-root",
            str(lock_root),
            "--ttl-min",
            "1",
            "--dry-run",
            "--format",
            "json",
        ]
    )
    assert exit_code == cli.EX_OK
    assert lock_path.exists()

    exit_code = cli.main(
        [
            "locks",
            "clean",
            "--lock-root",
            str(lock_root),
            "--ttl-min",
            "1",
            "--no-dry-run",
            "--format",
            "json",
        ]
    )
    assert exit_code == cli.EX_OK
    assert not lock_path.exists()
