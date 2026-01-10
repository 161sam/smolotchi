from __future__ import annotations

import json

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.jobs import JobStore
import smolotchi.cli as cli


def test_global_flags_parse_for_common_subcommands() -> None:
    parser = cli.build_parser()

    args = parser.parse_args(["--format", "json", "health"])
    assert args.format == "json"

    args = parser.parse_args(["--dry-run", "--format", "json", "prune"])
    assert args.dry_run is True
    assert args.format == "json"

    args = parser.parse_args(["--dry-run", "--format", "json", "job-delete", "job-123"])
    assert args.dry_run is True
    assert args.format == "json"


def test_health_json_output(tmp_path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    store = ArtifactStore(str(artifact_root))
    store.put_json(
        kind="worker_health",
        title="health",
        payload={"pid": 123, "job_id": "job-1", "ts": 123.0},
    )

    exit_code = cli.main(
        [
            "--format",
            "json",
            "--artifact-root",
            str(artifact_root),
            "health",
        ]
    )
    assert exit_code == cli.EX_OK
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["worker_artifact_id"]
    assert payload["worker_pid"] == 123
    assert payload["job_id"] == "job-1"


def test_job_delete_unknown_id_reports_validation_error(tmp_path, capsys) -> None:
    db_path = tmp_path / "jobs.db"
    exit_code = cli.main(
        [
            "--format",
            "json",
            "--db",
            str(db_path),
            "job-delete",
            "999999",
        ]
    )
    assert exit_code == cli.EX_VALIDATION
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["code"] == cli.EX_VALIDATION
    assert payload["message"]
    assert "details" in payload


def test_job_actions_dry_run_does_not_mutate(tmp_path, capsys) -> None:
    db_path = tmp_path / "jobs.db"
    store = JobStore(str(db_path))

    job_id = "job-delete"
    store.enqueue({"id": job_id, "kind": "test", "scope": "scope", "note": "", "meta": {}})
    exit_code = cli.main(
        [
            "--dry-run",
            "--format",
            "json",
            "--db",
            str(db_path),
            "job-delete",
            job_id,
        ]
    )
    assert exit_code == cli.EX_OK
    assert store.get(job_id) is not None
    capsys.readouterr()

    cancel_id = "job-cancel"
    store.enqueue(
        {"id": cancel_id, "kind": "test", "scope": "scope", "note": "", "meta": {}}
    )
    exit_code = cli.main(
        [
            "--dry-run",
            "--format",
            "json",
            "--db",
            str(db_path),
            "job-cancel",
            cancel_id,
        ]
    )
    assert exit_code == cli.EX_OK
    assert store.get(cancel_id).status == "queued"
    capsys.readouterr()

    reset_id = "job-reset"
    store.enqueue(
        {"id": reset_id, "kind": "test", "scope": "scope", "note": "", "meta": {}}
    )
    store.mark_running(reset_id)
    exit_code = cli.main(
        [
            "--dry-run",
            "--format",
            "json",
            "--db",
            str(db_path),
            "job-reset",
            reset_id,
        ]
    )
    assert exit_code == cli.EX_OK
    assert store.get(reset_id).status == "running"


def test_prune_dry_run_keeps_artifacts(tmp_path, capsys) -> None:
    artifact_root = tmp_path / "artifacts"
    store = ArtifactStore(str(artifact_root))
    meta = store.put_json(
        kind="lan_bundle",
        title="bundle",
        payload={"job_id": "job-1"},
    )

    index_path = store.index_path
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index[0]["created_ts"] = 0
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")

    exit_code = cli.main(
        [
            "--dry-run",
            "--format",
            "json",
            "--artifact-root",
            str(artifact_root),
            "--db",
            str(tmp_path / "events.db"),
            "--config",
            "config.toml",
            "prune",
        ]
    )
    assert exit_code == cli.EX_OK
    assert store.get_meta(meta.id) is not None
    assert (artifact_root / f"{meta.id}.json").exists()
    capsys.readouterr()
