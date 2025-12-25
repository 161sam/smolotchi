from __future__ import annotations

import time
from typing import Optional

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.core.engines import EngineHealth
from smolotchi.core.normalize import normalize_profile, profile_hash
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.engines.net_detect import detect_scope_for_iface
from smolotchi.engines.net_health import health_check
from smolotchi.engines.wifi_connect import connect_wpa_psk, disconnect_wpa
from smolotchi.engines.wifi_scan import scan_iw
from smolotchi.engines.wifi_targets import update_targets_state
from smolotchi.reports.wifi_session_report import wifi_session_html


class WifiEngine:
    name = "wifi"

    def __init__(self, bus: SQLiteBus, config: ConfigStore, artifacts: ArtifactStore):
        self.bus = bus
        self.config = config
        self.artifacts = artifacts
        self._running = False
        self._last_scan = 0.0
        self._last_health = 0.0
        self._last_health_ok = None
        self._connected_ssid: Optional[str] = None
        self._connected_profile: Optional[dict] = None
        self._session_started_ts = None
        self._session_id = None
        self._lan_busy = False
        self._lan_locked = False
        self._last_lan_evt_ts = 0.0
        self._forced_profile_ssid: Optional[str] = None

    def start(self) -> None:
        self._running = True
        cfg = self.config.get()
        self.bus.publish("wifi.engine.started", {"safe_mode": cfg.wifi.safe_mode})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("wifi.engine.stopped", {})

    def _tail_since(self, topic_prefix: str, last_ts: float, limit: int = 80):
        evts = self.bus.tail(limit=limit, topic_prefix=topic_prefix)
        out = []
        for e in evts:
            ts = getattr(e, "ts", 0.0) or 0.0
            if ts and ts > last_ts:
                out.append(e)
        out.sort(key=lambda e: getattr(e, "ts", 0.0) or 0.0)
        return out

    def _start_session(self, iface: str, ssid: str) -> None:
        self._connected_ssid = ssid
        self._session_started_ts = time.time()
        self._session_id = f"wifi-{int(self._session_started_ts)}"
        self.bus.publish(
            "wifi.session.start",
            {"id": self._session_id, "ssid": ssid, "iface": iface},
        )

    def _end_session(self, iface: str, reason: str) -> None:
        end_ts = time.time()
        start_ts = self._session_started_ts or end_ts
        duration = max(0.0, end_ts - start_ts)
        scope = detect_scope_for_iface(iface)
        if not self._session_id:
            self._session_id = f"wifi-{int(start_ts)}"
        payload = {
            "id": self._session_id,
            "iface": iface,
            "ssid": self._connected_ssid,
            "ts_start": start_ts,
            "ts_end": end_ts,
            "duration_sec": round(duration, 2),
            "scope": scope,
            "reason": reason,
        }

        try:
            art = self.artifacts.put_json(
                kind="wifi_session",
                title=f"wifi session {self._session_id}",
                payload=payload,
            )
            self.bus.publish(
                "wifi.session.saved", {"id": self._session_id, "artifact_id": art.id}
            )
            try:
                html = wifi_session_html(payload)
                html_id = self.artifacts.put_text(
                    kind="wifi_session_report",
                    title=f"wifi session report {self._session_id}",
                    text=html,
                    ext=".html",
                    mime="text/html; charset=utf-8",
                )
                self.bus.publish(
                    "wifi.session.report.saved",
                    {"id": self._session_id, "artifact_id": html_id.id},
                )
            except Exception as ex:
                self.bus.publish(
                    "wifi.session.report.save_failed",
                    {"id": self._session_id, "err": str(ex)},
                )
        except Exception as ex:
            self.bus.publish(
                "wifi.session.save_failed", {"id": self._session_id, "err": str(ex)}
            )

        self._session_started_ts = None
        self._session_id = None

    def tick(self) -> None:
        if not self._running:
            return

        cfg = self.config.get()
        w = cfg.wifi
        if not w.enabled:
            return

        iface = w.iface or "wlan0"
        now = time.time()

        evts = []
        evts += self._tail_since("ui.lan.", self._last_lan_evt_ts, limit=80)
        evts += self._tail_since("lan.", self._last_lan_evt_ts, limit=80)

        saw_lan_done = False
        for e in evts:
            self._last_lan_evt_ts = max(
                self._last_lan_evt_ts, getattr(e, "ts", 0.0) or 0.0
            )

            if e.topic == "ui.lan.enqueue":
                if not self._lan_busy:
                    self._lan_busy = True
                    self.bus.publish("wifi.lan.busy", {"reason": "ui.lan.enqueue"})
            elif e.topic in ("lan.job.started", "lan.job.running"):
                if not self._lan_busy:
                    self._lan_busy = True
                    self.bus.publish("wifi.lan.busy", {"reason": e.topic})
            elif e.topic in ("lan.done", "lan.job.done"):
                saw_lan_done = True
                if self._lan_busy:
                    self._lan_busy = False
                    self.bus.publish("wifi.lan.idle", {"reason": e.topic})

        profile = self._connected_profile or {}
        if "lock_during_lan" in profile:
            lock_during_lan = bool(profile.get("lock_during_lan"))
        else:
            lock_during_lan = bool(w.lock_during_lan)
        if "disconnect_after_lan" in profile:
            disconnect_after_lan = bool(profile.get("disconnect_after_lan"))
        else:
            disconnect_after_lan = bool(getattr(w, "disconnect_after_lan", False))

        if self._lan_busy and lock_during_lan:
            if not self._lan_locked:
                self.bus.publish("wifi.lock", {"reason": "lan_busy"})
            self._lan_locked = True
        else:
            if self._lan_locked:
                self.bus.publish("wifi.unlock", {"reason": "lan_idle"})
            self._lan_locked = False

        if (
            saw_lan_done
            and disconnect_after_lan
            and self._connected_ssid
            and (not self._lan_locked)
        ):
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
            self._end_session(iface, "lan_done")
            self._connected_ssid = None
            self._connected_profile = None

        ui_evts = self.bus.tail(limit=20, topic_prefix="ui.wifi.")
        app = next((e for e in ui_evts if e.topic == "ui.wifi.profile.apply"), None)
        if app and app.payload:
            self._forced_profile_ssid = (app.payload.get("ssid") or "").strip() or None
            self.bus.publish(
                "wifi.profile.selected", {"ssid": self._forced_profile_ssid}
            )
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
                    profiles = getattr(w, "profiles", None) or {}
                    profile = {}
                    if isinstance(profiles, dict):
                        profile = profiles.get(ssid) or {}
                    if not isinstance(profile, dict):
                        profile = {}
                    apply_on_connect = bool(
                        getattr(w, "apply_profile_on_connect", True)
                    )
                    self._connected_profile = profile if apply_on_connect else {}
                    self._start_session(iface_req, ssid)
                    if self._forced_profile_ssid == ssid:
                        self._forced_profile_ssid = None

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
                self._end_session(iface, "ui_request")
                self._connected_ssid = None
                self._connected_profile = None

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
                    self._end_session(iface, "health_failed")
                    self._connected_ssid = None
                    self._connected_profile = None

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
                                profiles = getattr(w, "profiles", None) or {}
                                profile = {}
                                if isinstance(profiles, dict):
                                    profile = profiles.get(ssid) or {}
                                if not isinstance(profile, dict):
                                    profile = {}
                                apply_on_connect = bool(
                                    getattr(w, "apply_profile_on_connect", True)
                                )
                                self._connected_profile = (
                                    profile if apply_on_connect else {}
                                )
                                self._start_session(iface, ssid)

        if self._lan_locked and self._connected_ssid:
            return

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

        try:
            existing_id = self.artifacts.find_latest(kind="wifi_targets")
        except Exception:
            existing_id = None

        state = {}
        if existing_id:
            state = self.artifacts.get_json(existing_id) or {}

        aps_payload = [
            {
                "ssid": ap.ssid,
                "bssid": ap.bssid,
                "freq": ap.freq_mhz,
                "signal": ap.signal_dbm,
                "sec": ap.security,
            }
            for ap in aps[:80]
        ]

        new_state = update_targets_state(state, aps_payload)
        tid = self.artifacts.put_json(
            kind="wifi_targets", title="wifi targets (memory)", payload=new_state
        )
        self.bus.publish(
            "wifi.targets.saved",
            {"artifact_id": tid.id, "count": len(new_state.get("targets") or {})},
        )

        if not w.auto_connect:
            return
        if self._lan_locked:
            return

        allow = set(w.allow_ssids or [])
        creds = w.credentials or {}
        forced = (self._forced_profile_ssid or "").strip()

        preferred = w.preferred_ssid or ""
        chosen = None
        for ap in aps:
            if not ap.ssid:
                continue
            if forced and ap.ssid != forced:
                continue
            if allow and ap.ssid not in allow:
                continue
            if ap.ssid in creds:
                if forced and ap.ssid == forced:
                    chosen = ap.ssid
                    break
                if preferred and ap.ssid == preferred:
                    chosen = ap.ssid
                    break
                chosen = chosen or ap.ssid

        if not chosen:
            return

        if self._connected_ssid == chosen:
            return

        profiles = getattr(w, "profiles", None) or {}
        profile = {}
        if isinstance(profiles, dict):
            profile = profiles.get(chosen) or {}
        if not isinstance(profile, dict):
            profile = {}
        profile_norm, warnings = normalize_profile(profile)
        prof_hash = profile_hash(profile_norm)
        apply_on_connect = bool(getattr(w, "apply_profile_on_connect", True))

        ok, out = connect_wpa_psk(iface, chosen, creds[chosen])
        self.bus.publish(
            "wifi.connect",
            {"iface": iface, "ssid": chosen, "ok": ok, "note": out[-500:]},
        )
        if not ok:
            return

        self._connected_profile = profile_norm if apply_on_connect else {}
        self._start_session(iface, chosen)
        scope_map = getattr(w, "scope_map", None) or {}
        mapped = (
            (scope_map.get(chosen) or "").strip()
            if isinstance(scope_map, dict)
            else ""
        )
        p_scope = (profile_norm.get("scope") or "").strip() if apply_on_connect else ""
        scope = (
            p_scope
            or mapped
            or detect_scope_for_iface(iface)
            or getattr(getattr(cfg, "lan", None), "default_scope", "10.0.10.0/24")
        )
        lan_overrides = {}
        if apply_on_connect:
            if profile_norm.get("lan_pack"):
                lan_overrides["pack"] = profile_norm.get("lan_pack")
            if profile_norm.get("lan_throttle_rps") is not None:
                lan_overrides["throttle_rps"] = profile_norm.get("lan_throttle_rps")
            if profile_norm.get("lan_batch_size") is not None:
                lan_overrides["batch_size"] = profile_norm.get("lan_batch_size")
        if apply_on_connect:
            self.bus.publish(
                "lan.profile.applied",
                {
                    "ssid": chosen,
                    "hash": prof_hash,
                    "warnings": warnings,
                    "ts": time.time(),
                },
            )
        job_id = f"job-{int(time.time())}"
        if apply_on_connect:
            self.artifacts.put_json(
                kind="profile_timeline",
                title=f"Profile applied • {chosen}",
                payload={
                    "ssid": chosen,
                    "profile_hash": prof_hash,
                    "profile": profile_norm,
                    "applied_at": time.time(),
                    "job_id": job_id,
                    "bundle_id": None,
                    "reason": "wifi_connect",
                },
            )
        self.bus.publish(
            "ui.lan.enqueue",
            {
                "job": {
                    "id": job_id,
                    "kind": "inventory",
                    "scope": scope,
                    "note": f"triggered by wifi ssid={chosen} iface={iface}",
                    "meta": {
                        "wifi_ssid": chosen,
                        "wifi_iface": iface,
                        "wifi_profile": profile_norm if apply_on_connect else {},
                        "wifi_profile_hash": prof_hash if apply_on_connect else None,
                        "lan_overrides": lan_overrides,
                    },
                }
            },
        )
        if self._forced_profile_ssid == chosen:
            self._forced_profile_ssid = None

    def health(self) -> EngineHealth:
        cfg = self.config.get()
        if not cfg.wifi.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        detail = "running" if self._running else "stopped"
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
