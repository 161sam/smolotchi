from __future__ import annotations

from pathlib import Path

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.dossier import build_lan_dossier
from smolotchi.core.jobs import JobStore
from smolotchi.core.lan_resolver import resolve_result_by_job_id


def test_build_lan_dossier_creates_artifact(tmp_path: Path) -> None:
    db_path = tmp_path / "events.db"
    art_root = tmp_path / "artifacts"

    jobstore = JobStore(str(db_path))
    job_id = "job-123"
    scope = "10.0.0.0/24"
    jobstore.enqueue(
        {
            "id": job_id,
            "kind": "inventory",
            "scope": scope,
            "note": "",
        }
    )

    artifacts = ArtifactStore(str(art_root))
    artifacts.put_json(
        kind="wifi_lan_timeline",
        title="wifi→lan test",
        payload={
            "ts": 1.0,
            "ssid": "TestNet",
            "iface": "wlan0",
            "job_id": job_id,
            "scope": scope,
            "reason": "test",
        },
    )
    bundle_meta = artifacts.put_json(
        kind="lan_bundle",
        title=f"Bundle • {job_id}",
        payload={"job_id": job_id, "result_json": {"artifact_id": "json-id"}},
    )
    report_meta = artifacts.put_text(
        kind="lan_report", title="Report • test", text="report", ext=".html"
    )
    artifacts.put_json(
        kind="lan_job_result",
        title=f"lan job result {job_id}",
        payload={
            "ts": 2.0,
            "job_id": job_id,
            "bundle_id": bundle_meta.id,
            "report_id": report_meta.id,
            "ok": True,
        },
    )

    dossier_id = build_lan_dossier(
        job_id=job_id,
        scope="",
        reason="test",
        artifacts=artifacts,
        jobstore=jobstore,
        resolve_result_by_job_id=resolve_result_by_job_id,
    )
    payload = artifacts.get_json(dossier_id)

    assert payload
    assert payload["job_id"] == job_id
    assert payload["scope"] == scope
    assert payload["wifi"]["ssid"] == "TestNet"
    assert payload["lan"]["bundle_id"] == bundle_meta.id
    assert payload["lan"]["report_id"] == report_meta.id
