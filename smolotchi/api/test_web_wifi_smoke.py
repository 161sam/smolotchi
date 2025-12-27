from __future__ import annotations

from pathlib import Path

from smolotchi.api import web


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
