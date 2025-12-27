from __future__ import annotations

import time
from pathlib import Path

import smolotchi.engines.wifi_engine as wifi_engine
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.engines.wifi_engine import WifiEngine


def _write_config(path: Path) -> None:
    path.write_text(
        """
[wifi]
enabled = true
iface = "wlan0"
scan_interval_sec = 9999999999
auto_connect = false
health_enabled = false
apply_profile_on_connect = true
allow_ssids = ["TestNet"]
credentials = { "TestNet" = "pass" }
profiles = { "TestNet" = { scope = "10.0.10.0/24" } }
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _make_engine(tmp_path: Path) -> tuple[WifiEngine, SQLiteBus, ArtifactStore]:
    config_path = tmp_path / "config.toml"
    _write_config(config_path)
    store = ConfigStore(str(config_path))
    store.load()
    bus = SQLiteBus(str(tmp_path / "events.db"))
    artifacts = ArtifactStore(str(tmp_path / "artifacts"))
    engine = WifiEngine(bus, store, artifacts)
    engine.start()
    return engine, bus, artifacts


def test_wifi_profile_selection_artifact(tmp_path: Path) -> None:
    engine, bus, artifacts = _make_engine(tmp_path)

    bus.publish("ui.wifi.profile.apply", {"ssid": "TestNet", "iface": "wlan0"})
    engine.tick()

    selections = artifacts.list(kind="wifi_profile_selection", limit=5)
    assert len(selections) == 1
    payload = artifacts.get_json(selections[0].id)
    assert payload
    assert payload["ssid"] == "TestNet"
    assert payload["source"] == "ui"
    assert payload.get("wifi_profile_hash")


def test_wifi_connect_artifacts(tmp_path: Path, monkeypatch) -> None:
    engine, bus, artifacts = _make_engine(tmp_path)

    monkeypatch.setattr(
        wifi_engine,
        "connect_wpa_psk",
        lambda iface, ssid, psk: (True, "ok"),
    )

    bus.publish("ui.wifi.connect", {"ssid": "TestNet", "iface": "wlan0"})
    engine.tick()

    attempts = artifacts.list(kind="wifi_connect_attempt", limit=5)
    results = artifacts.list(kind="wifi_connect_result", limit=5)
    assert len(attempts) == 1
    assert len(results) == 1

    attempt_payload = artifacts.get_json(attempts[0].id)
    result_payload = artifacts.get_json(results[0].id)
    assert attempt_payload
    assert result_payload
    assert attempt_payload["ok"] is None
    assert attempt_payload["allowed"] is True
    assert attempt_payload["has_cred"] is True
    assert result_payload["ok"] is True
    assert result_payload.get("wifi_profile_hash")


def test_wifi_disconnect_artifacts(tmp_path: Path, monkeypatch) -> None:
    engine, bus, artifacts = _make_engine(tmp_path)
    engine._connected_ssid = "TestNet"
    engine._session_started_ts = time.time()
    engine._session_id = "wifi-123"

    monkeypatch.setattr(
        wifi_engine, "detect_scope_for_iface", lambda iface: "10.0.10.0/24"
    )
    monkeypatch.setattr(wifi_engine, "disconnect_wpa", lambda iface: (True, "ok"))

    bus.publish("ui.wifi.disconnect", {"iface": "wlan0"})
    engine.tick()

    attempts = artifacts.list(kind="wifi_disconnect_attempt", limit=5)
    results = artifacts.list(kind="wifi_disconnect_result", limit=5)
    assert len(attempts) == 1
    assert len(results) == 1

    attempt_payload = artifacts.get_json(attempts[0].id)
    result_payload = artifacts.get_json(results[0].id)
    assert attempt_payload
    assert result_payload
    assert attempt_payload["ok"] is None
    assert result_payload["ok"] is True


def test_wifi_ui_connect_enqueues_lan_and_records_timeline(
    tmp_path: Path, monkeypatch
) -> None:
    engine, bus, artifacts = _make_engine(tmp_path)

    monkeypatch.setattr(wifi_engine, "connect_wpa_psk", lambda iface, ssid, psk: (True, "ok"))
    monkeypatch.setattr(
        wifi_engine, "detect_scope_for_iface", lambda iface: "10.0.10.0/24"
    )

    bus.publish("ui.wifi.connect", {"ssid": "TestNet", "iface": "wlan0"})
    engine.tick()

    timeline = artifacts.list(kind="wifi_lan_timeline", limit=5)
    assert len(timeline) == 1
    timeline_payload = artifacts.get_json(timeline[0].id)
    assert timeline_payload
    assert timeline_payload.get("job_id")

    results = artifacts.list(kind="wifi_connect_result", limit=5)
    result_payload = artifacts.get_json(results[0].id)
    assert result_payload
    assert result_payload.get("job_id") == timeline_payload.get("job_id")

    evts = bus.tail(limit=50, topic_prefix="ui.lan.")
    assert any(
        e.topic == "ui.lan.enqueue"
        and (e.payload.get("job") or {}).get("id") == timeline_payload["job_id"]
        for e in evts
    )
