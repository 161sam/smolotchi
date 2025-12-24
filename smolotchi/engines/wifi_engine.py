from __future__ import annotations

import time
from typing import Optional

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.core.engines import EngineHealth
from smolotchi.core.jobs import JobStore
from smolotchi.core.lan_state import lan_is_busy
from smolotchi.engines.net_detect import detect_scope_for_iface
from smolotchi.engines.net_health import health_check
from smolotchi.engines.wifi_connect import connect_wpa_psk, disconnect_wpa
from smolotchi.engines.wifi_scan import scan_iw


class WifiEngine:
    name = "wifi"

    def __init__(self, bus: SQLiteBus, config: ConfigStore, jobstore: JobStore):
        self.bus = bus
        self.config = config
        self.jobstore = jobstore
        self._running = False
        self._last_scan = 0.0
        self._last_health = 0.0
        self._last_health_ok = None
        self._connected_ssid: Optional[str] = None
        self._lan_locked = False
        self._lan_was_busy = False
        self._last_lan_done_ts = 0.0

    def _maybe_disconnect_after_lan(
        self, busy: bool, lan_was_busy: bool, iface: str, w
    ) -> None:
        if (
            self._connected_ssid
            and (not busy)
            and lan_was_busy
            and w.disconnect_after_lan
        ):
            ok, out = disconnect_wpa(iface)
            self.bus.publish(
                "wifi.disconnect",
                {"iface": iface, "ssid": self._connected_ssid, "ok": ok, "note": out},
            )
            self._connected_ssid = None

    def _lan_done_event_since_last(self) -> bool:
        for evt in self.bus.tail(limit=40, topic_prefix="lan."):
            if evt.topic in ("lan.done", "lan.job.done") and evt.ts > self._last_lan_done_ts:
                self._last_lan_done_ts = evt.ts
                return True

        for evt in self.bus.tail(limit=40, topic_prefix="ui.lan."):
            if evt.topic == "ui.lan.done" and evt.ts > self._last_lan_done_ts:
                self._last_lan_done_ts = evt.ts
                return True
        return False

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

        busy = lan_is_busy(self.jobstore)
        lan_was_busy = self._lan_was_busy
        self._lan_was_busy = busy
        if busy and w.lock_during_lan:
            if not self._lan_locked:
                self.bus.publish("wifi.lock", {"reason": "lan_busy"})
            self._lan_locked = True
        else:
            if self._lan_locked:
                self.bus.publish("wifi.unlock", {"reason": "lan_idle"})
            self._lan_locked = False

        iface = w.iface or "wlan0"

        ui_evts = self.bus.tail(limit=20, topic_prefix="ui.wifi.")
        req = next((e for e in ui_evts if e.topic == "ui.wifi.connect"), None)
        if req and req.payload and not self._lan_locked:
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

        dis = next((e for e in ui_evts if e.topic == "ui.wifi.disconnect"), None)
        if dis and dis.payload:
            if self._lan_locked:
                self.bus.publish(
                    "wifi.disconnect",
                    {
                        "iface": iface,
                        "ssid": self._connected_ssid,
                        "ok": False,
                        "reason": "lan_locked",
                    },
                )
            elif self._connected_ssid:
                ok, out = disconnect_wpa(iface)
                self.bus.publish(
                    "wifi.disconnect",
                    {
                        "iface": iface,
                        "ssid": self._connected_ssid,
                        "ok": ok,
                        "reason": "ui_request",
                        "note": out,
                    },
                )
                if ok:
                    self._connected_ssid = None

        if self._connected_ssid and getattr(w, "disconnect_after_lan", False):
            if (not self._lan_locked) and self._lan_done_event_since_last():
                ok, out = disconnect_wpa(iface)
                self.bus.publish(
                    "wifi.disconnect",
                    {
                        "iface": iface,
                        "ssid": self._connected_ssid,
                        "ok": ok,
                        "reason": "lan_done",
                        "note": out,
                    },
                )
                self._connected_ssid = None

        if self._connected_ssid and getattr(w, "health_enabled", True):
            interval = int(getattr(w, "health_interval_sec", 20) or 20)
            if time.time() - self._last_health >= interval:
                self._last_health = time.time()
                h = health_check(
                    iface,
                    ping_gateway=bool(getattr(w, "health_ping_gateway", True)),
                    ping_target=(getattr(w, "health_ping_target", None) or None),
                )
                self._last_health_ok = h["ok"]
                self.bus.publish("wifi.health", h)

                if (
                    (not h["ok"])
                    and bool(getattr(w, "auto_disconnect_on_broken", True))
                    and (not self._lan_locked)
                ):
                    ssid = self._connected_ssid
                    ok, out = disconnect_wpa(iface)
                    self.bus.publish(
                        "wifi.disconnect",
                        {
                            "iface": iface,
                            "ssid": ssid,
                            "ok": ok,
                            "reason": "health_failed",
                        },
                    )
                    self._connected_ssid = None

                    if bool(getattr(w, "auto_reconnect_on_broken", False)):
                        creds = getattr(w, "credentials", None) or {}
                        if ssid and ssid in creds:
                            ok2, out2 = connect_wpa_psk(iface, ssid, creds[ssid])
                            self.bus.publish(
                                "wifi.connect",
                                {
                                    "iface": iface,
                                    "ssid": ssid,
                                    "ok": ok2,
                                    "note": out2[-500:],
                                },
                            )
                            if ok2:
                                self._connected_ssid = ssid

        if self._lan_locked and self._connected_ssid:
            return

        now = time.time()
        if now - self._last_scan < w.scan_interval_sec:
            self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)
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
            self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)
            return
        if self._lan_locked:
            self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)
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
            self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)
            return

        if self._connected_ssid == chosen:
            self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)
            return

        ok, out = connect_wpa_psk(iface, chosen, creds[chosen])
        self.bus.publish(
            "wifi.connect",
            {"iface": iface, "ssid": chosen, "ok": ok, "note": out[-500:]},
        )
        if not ok:
            self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)
            return

        self._connected_ssid = chosen
        scope_map = getattr(w, "scope_map", None) or {}
        mapped = (
            (scope_map.get(chosen) or "").strip()
            if isinstance(scope_map, dict)
            else ""
        )
        scope = mapped or detect_scope_for_iface(iface) or getattr(
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
        self._maybe_disconnect_after_lan(busy, lan_was_busy, iface, w)

    def health(self) -> EngineHealth:
        cfg = self.config.get()
        if not cfg.wifi.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        detail = "running" if self._running else "stopped"
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
