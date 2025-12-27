from __future__ import annotations

from pathlib import Path

from smolotchi.api import web
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.jobs import JobStore


def test_wifi_page_renders(tmp_path: Path, monkeypatch) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[wifi]
enabled = true
iface = "wlan0"
scan_interval_sec = 9999999999
auto_connect = false
health_enabled = false

[lan]
default_scope = "10.0.10.0/24"
default_pack = "bjorn_core"
throttle_rps = 1.0
batch_size = 4
""".strip()
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("SMOLOTCHI_DB", str(tmp_path / "events.db"))
    monkeypatch.setenv("SMOLOTCHI_ARTIFACT_ROOT", str(tmp_path / "artifacts"))

    monkeypatch.setattr(web, "detect_ipv4_cidr", lambda iface: None)
    monkeypatch.setattr(web, "detect_scope_for_iface", lambda iface: None)

    app = web.create_app(str(cfg))
    client = app.test_client()
    resp = client.get("/wifi")
    assert resp.status_code == 200
    assert b"WiFi" in resp.data


def test_wifi_lan_timeline_shows_done_when_jobstore_done(
    tmp_path: Path, monkeypatch
) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[wifi]
enabled = true
iface = "wlan0"
scan_interval_sec = 9999999999
auto_connect = false
health_enabled = false

[lan]
default_scope = "10.0.10.0/24"
default_pack = "bjorn_core"
throttle_rps = 1.0
batch_size = 4
""".strip()
        + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "events.db"
    art_root = tmp_path / "artifacts"
    monkeypatch.setenv("SMOLOTCHI_DB", str(db_path))
    monkeypatch.setenv("SMOLOTCHI_ARTIFACT_ROOT", str(art_root))

    monkeypatch.setattr(web, "detect_ipv4_cidr", lambda iface: None)
    monkeypatch.setattr(web, "detect_scope_for_iface", lambda iface: None)

    job_id = "job-test-1"
    jobstore = JobStore(str(db_path))
    jobstore.enqueue(
        {
            "id": job_id,
            "kind": "inventory",
            "scope": "10.0.10.0/24",
            "note": "test",
            "meta": {},
        }
    )
    jobstore.mark_done(job_id)

    artifacts = ArtifactStore(str(art_root))
    artifacts.put_json(
        kind="wifi_lan_timeline",
        title=f"wifi→lan TestNet {job_id}",
        payload={
            "ts": 123.0,
            "ssid": "TestNet",
            "iface": "wlan0",
            "wifi_profile_hash": None,
            "job_id": job_id,
            "scope": "10.0.10.0/24",
            "lan_overrides": {},
            "reason": "test",
        },
    )

    app = web.create_app(str(cfg))
    client = app.test_client()
    resp = client.get("/wifi")

    assert resp.status_code == 200
    assert b">done<" in resp.data


def test_resolve_result_by_job_id_prefers_lan_job_result(
    tmp_path: Path, monkeypatch
) -> None:
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        """
[wifi]
enabled = true
iface = "wlan0"
scan_interval_sec = 9999999999
auto_connect = false
health_enabled = false

[lan]
default_scope = "10.0.10.0/24"
default_pack = "bjorn_core"
throttle_rps = 1.0
batch_size = 4
""".strip()
        + "\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "events.db"
    art_root = tmp_path / "artifacts"
    monkeypatch.setenv("SMOLOTCHI_DB", str(db_path))
    monkeypatch.setenv("SMOLOTCHI_ARTIFACT_ROOT", str(art_root))

    app = web.create_app(str(cfg))
    artifacts = ArtifactStore(str(art_root))
    job_id = "job-123"

    report_old = artifacts.put_text(
        kind="lan_report", title="Report • old", text="<html>old</html>", ext=".html"
    )
    bundle_meta = artifacts.put_json(
        kind="lan_bundle",
        title=f"Bundle • {job_id}",
        payload={
            "job_id": job_id,
            "kind": "inventory",
            "scope": "10.0.10.0/24",
            "created_ts": 1.0,
            "report_html": {"artifact_id": report_old.id, "path": report_old.path},
        },
    )

    report_new = artifacts.put_text(
        kind="lan_report", title="Report • new", text="<html>new</html>", ext=".html"
    )
    artifacts.put_json(
        kind="lan_job_result",
        title=f"lan job result {job_id}",
        payload={
            "ts": 2.0,
            "job_id": job_id,
            "bundle_id": bundle_meta.id,
            "report_id": report_new.id,
            "ok": True,
        },
    )

    resolved = app.resolve_result_by_job_id(job_id)
    assert resolved.get("bundle_id") == bundle_meta.id
    assert resolved.get("report_id") == report_new.id
