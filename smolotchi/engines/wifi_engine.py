from __future__ import annotations

import time
from typing import Optional

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.core.engines import EngineHealth
from smolotchi.engines.net_detect import detect_scope_for_iface
from smolotchi.engines.wifi_connect import connect_wpa_psk
from smolotchi.engines.wifi_scan import scan_iw


class WifiEngine:
    name = "wifi"

    def __init__(self, bus: SQLiteBus, config: ConfigStore):
        self.bus = bus
        self.config = config
        self._running = False
        self._last_scan = 0.0
        self._connected_ssid: Optional[str] = None

    def start(self) -> None:
        self._running = True
        cfg = self.config.get()
        self.bus.publish("wifi.engine.started", {"safe_mode": cfg.wifi.safe_mode})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("wifi.engine.stopped", {})

    def tick(self) -> None:
        if not self._running:
            return

        cfg = self.config.get()
        w = cfg.wifi
        if not w.enabled:
            return

        iface = w.iface or "wlan0"
        ui_evts = self.bus.tail(limit=20, topic_prefix="ui.wifi.")
        req = next((e for e in ui_evts if e.topic == "ui.wifi.connect"), None)
        if req and req.payload:
            ssid = (req.payload.get("ssid") or "").strip()
            iface_req = (req.payload.get("iface") or iface).strip()
            creds = w.credentials or {}
            allow = set(w.allow_ssids or [])
            if ssid and ssid in creds and ((not allow) or ssid in allow):
                ok, out = connect_wpa_psk(iface_req, ssid, creds[ssid])
                self.bus.publish(
                    "wifi.connect",
                    {
                        "iface": iface_req,
                        "ssid": ssid,
                        "ok": ok,
                        "note": out[-500:],
                    },
                )
                if ok:
                    self._connected_ssid = ssid

        now = time.time()
        if now - self._last_scan < w.scan_interval_sec:
            return
        self._last_scan = now

        aps = scan_iw(iface)

        self.bus.publish(
            "wifi.scan",
            {
                "iface": iface,
                "count": len(aps),
                "aps": [
                    {
                        "ssid": ap.ssid,
                        "bssid": ap.bssid,
                        "freq": ap.freq_mhz,
                        "signal": ap.signal_dbm,
                        "sec": ap.security,
                    }
                    for ap in aps[:30]
                ],
            },
        )

        if not w.auto_connect:
            return

        allow = set(w.allow_ssids or [])
        creds = w.credentials or {}

        preferred = w.preferred_ssid or ""
        chosen = None
        for ap in aps:
            if not ap.ssid:
                continue
            if allow and ap.ssid not in allow:
                continue
            if ap.ssid in creds:
                if preferred and ap.ssid == preferred:
                    chosen = ap.ssid
                    break
                chosen = chosen or ap.ssid

        if not chosen:
            return

        if self._connected_ssid == chosen:
            return

        ok, out = connect_wpa_psk(iface, chosen, creds[chosen])
        self.bus.publish(
            "wifi.connect",
            {"iface": iface, "ssid": chosen, "ok": ok, "note": out[-500:]},
        )
        if not ok:
            return

        self._connected_ssid = chosen
        scope = detect_scope_for_iface(iface) or getattr(
            getattr(cfg, "lan", None), "default_scope", "10.0.10.0/24"
        )
        self.bus.publish(
            "ui.lan.enqueue",
            {
                "job": {
                    "id": f"job-{int(time.time())}",
                    "kind": "inventory",
                    "scope": scope,
                    "note": f"triggered by wifi ssid={chosen} iface={iface}",
                }
            },
        )

    def health(self) -> EngineHealth:
        cfg = self.config.get()
        if not cfg.wifi.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        detail = "running" if self._running else "stopped"
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
