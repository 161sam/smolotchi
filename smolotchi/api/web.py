import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from flask import (
    Flask,
    Response,
    abort,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)

from smolotchi.api.health import core_health_ok, worker_health_ok
from smolotchi.api.theme import load_theme_tokens, tokens_to_css_vars
from smolotchi.api.view_models import effective_lan_overrides
from smolotchi.actions.registry import ActionRegistry, load_pack
from smolotchi.actions.planners.ai_planner import AIPlanner
from smolotchi.actions.runner import ActionRunner
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.config import ConfigStore
from smolotchi.core.policy import Policy
from smolotchi.core.presets import PRESETS
from smolotchi.core.paths import resolve_artifact_root, resolve_db_path
from smolotchi.core.normalize import normalize_profile, profile_hash
from smolotchi.core.validate import validate_profiles
from smolotchi.core.toml_patch import (
    cleanup_baseline_profiles,
    cleanup_baseline_scopes,
    patch_baseline_add,
    patch_baseline_remove,
    patch_baseline_profile_add,
    patch_baseline_profile_remove,
    patch_lan_lists,
    patch_wifi_allow_add,
    patch_wifi_allow_remove,
    parse_wifi_credentials_text,
    patch_wifi_credentials,
    parse_wifi_profiles_text,
    patch_wifi_profiles_set,
    patch_wifi_profile_upsert,
    patch_wifi_scope_map_remove,
    patch_wifi_scope_map_set,
)
from smolotchi.engines.net_detect import detect_ipv4_cidr, detect_scope_for_iface
from smolotchi.reports.exec_summary import (
    build_exec_summary,
    render_exec_summary_html,
    render_exec_summary_md,
)
from smolotchi.reports.host_diff import host_diff_html, host_diff_markdown
from smolotchi.reports.baseline import (
    expected_findings_for_bundle,
    expected_findings_for_profile,
    expected_findings_for_scope,
    profile_key_for_job_meta,
)
from smolotchi.reports.baseline_diff import compute_baseline_diff
from smolotchi.reports.top_findings import aggregate_top_findings


def pretty(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True)


def _atomic_write_text(path: Path, text: str) -> None:
    path = path.resolve()
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def create_app(config_path: str = "config.toml") -> Flask:
    app = Flask(__name__)
    db_path = resolve_db_path()
    artifact_root = resolve_artifact_root()

    bus = SQLiteBus(db_path=db_path)
    store = ConfigStore(config_path)
    store.load()
    artifacts = ArtifactStore(artifact_root)
    jobstore = JobStore(db_path)
    pack_path = Path(__file__).resolve().parents[1] / "actions" / "packs" / "bjorn_core.yml"
    registry = load_pack(str(pack_path)) if pack_path.exists() else ActionRegistry()

    def nav_active(endpoint: str) -> str:
        return "active" if request.endpoint == endpoint else ""

    def fmt_ts(ts: float | None) -> str:
        if not ts:
            return "-"
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))

    def core_recently_active(window_s: float = 30.0) -> tuple[bool, float | None]:
        now = time.time()
        events = bus.tail(limit=5, topic_prefix="core.health")
        if not events:
            return False, None
        last_ts = float(events[0].ts)
        return (now - last_ts) <= window_s, last_ts

    def _build_policy(cfg) -> Policy:
        policy_cfg = getattr(cfg, "policy", None)
        if not policy_cfg:
            return Policy()
        return Policy(
            allowed_tags=list(getattr(policy_cfg, "allowed_tags", []) or []),
            allowed_scopes=list(getattr(policy_cfg, "allowed_scopes", []) or []),
            allowed_tools=list(getattr(policy_cfg, "allowed_tools", []) or []),
            block_categories=list(getattr(policy_cfg, "block_categories", []) or []),
            autonomous_categories=list(
                getattr(policy_cfg, "autonomous_categories", []) or []
            ),
        )

    def _safe_store_path(root: str | Path, stored_path: str | Path) -> Path:
        if not stored_path:
            abort(404)
        root_p = Path(root).resolve()
        p = Path(stored_path)

        if not p.is_absolute():
            p = root_p / p

        p = p.resolve()
        try:
            p.relative_to(root_p)
        except ValueError:
            abort(404)

        if not p.exists() or not p.is_file():
            abort(404)

        return p

    @app.context_processor
    def inject_globals():
        cfg = store.get()
        tokens = {}
        if cfg.theme and cfg.theme.json_path:
            tokens = load_theme_tokens(cfg.theme.json_path)
        theme_css = tokens_to_css_vars(tokens) if tokens else ""
        core_ok, core_last_ts = core_health_ok(bus)
        worker_ok, worker_last_ts = worker_health_ok(artifacts)
        return {
            "nav_active": nav_active,
            "app_cfg": cfg,
            "config_path": config_path,
            "theme_css": theme_css,
            "core_ok": core_ok,
            "core_last_ts": core_last_ts,
            "worker_ok": worker_ok,
            "worker_last_ts": worker_last_ts,
            "fmt_ts": fmt_ts,
        }

    @app.get("/")
    def dashboard():
        events = bus.tail(limit=30)
        status_evt = next(
            (event for event in events if event.topic == "core.state.changed"), None
        )
        health_evts = bus.tail(limit=10, topic_prefix="core.health")
        health_evt = health_evts[0] if health_evts else None
        return render_template(
            "dashboard.html",
            status_evt=status_evt,
            health_evt=health_evt,
            events=events,
        )

    @app.get("/wifi")
    def wifi():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        iface = getattr(w, "iface", "wlan0") if w else "wlan0"
        ip_cidr = detect_ipv4_cidr(iface)
        scope = detect_scope_for_iface(iface)
        profiles_error = request.args.get("profiles_error") == "1"

        events_wifi = bus.tail(limit=80, topic_prefix="wifi.")
        events_ui = bus.tail(limit=40, topic_prefix="ui.")
        events_lan = bus.tail(limit=40, topic_prefix="lan.")
        events = events_wifi + events_ui + events_lan
        events = sorted(events, key=lambda e: e.ts, reverse=True)[:120]
        scan_evt = next((e for e in events if e.topic == "wifi.scan"), None)
        conn_evt = next((e for e in events if e.topic == "wifi.connect"), None)
        health_evt = next((e for e in events if e.topic == "wifi.health"), None)
        locked_evt = next((e for e in events if e.topic == "wifi.lock"), None)
        unlocked_evt = next((e for e in events if e.topic == "wifi.unlock"), None)
        lan_locked = bool(locked_evt) and (
            not unlocked_evt or locked_evt.ts > unlocked_evt.ts
        )

        aps = []
        if scan_evt and scan_evt.payload:
            aps = (scan_evt.payload.get("aps") or [])[:50]

        allow = set(getattr(w, "allow_ssids", []) or []) if w else set()
        scope_map = getattr(w, "scope_map", None) or {}
        if not isinstance(scope_map, dict):
            scope_map = {}
        profiles = getattr(w, "profiles", None) or {}
        if not isinstance(profiles, dict):
            profiles = {}
        profile_hashes = {}
        for ssid, prof in profiles.items():
            norm, _ = normalize_profile(prof if isinstance(prof, dict) else {})
            profile_hashes[ssid] = profile_hash(norm)
        creds = getattr(w, "credentials", None) or {}
        auto_connect = bool(getattr(w, "auto_connect", False)) if w else False
        preferred = (getattr(w, "preferred_ssid", "") or "").strip() if w else ""
        selected_profile_evt = next(
            (e for e in events if e.topic == "wifi.profile.selected"), None
        )
        sessions = artifacts.list(limit=10, kind="wifi_session")
        reports = artifacts.list(limit=20, kind="wifi_session_report")
        rep_map = {}
        for r in reports:
            rep_map[r.title.replace("wifi session report ", "").strip()] = r.id

        for s in sessions:
            sid = s.title.replace("wifi session ", "").strip()
            setattr(s, "report_id", rep_map.get(sid))

        targets_latest = artifacts.list(limit=1, kind="wifi_targets")
        targets_state = (
            artifacts.get_json(targets_latest[0].id) if targets_latest else {}
        )
        targets = (
            (targets_state.get("targets") or {})
            if isinstance(targets_state, dict)
            else {}
        )

        for ap in aps:
            ssid = (ap.get("ssid") or "").strip()
            bssid = (ap.get("bssid") or "").strip()
            mem = targets.get(bssid) or {}
            ap["_allowed"] = (not allow) or (ssid in allow)
            ap["_has_cred"] = ssid in creds
            ap["_preferred"] = bool(preferred and ssid == preferred)
            ap["_seen_count"] = mem.get("seen_count")
            ap["_strongest"] = mem.get("strongest_signal_dbm")
            ap["_last_seen_ts"] = mem.get("last_seen_ts")
            ap["_mapped_scope"] = (scope_map.get(ssid) or "").strip() if ssid else ""

        return render_template(
            "wifi.html",
            events=events,
            iface=iface,
            ip_cidr=ip_cidr,
            scope=scope,
            aps=aps,
            scan_evt=scan_evt,
            conn_evt=conn_evt,
            health_evt=health_evt,
            auto_connect=auto_connect,
            preferred_ssid=preferred,
            lan_locked=lan_locked,
            sessions=sessions,
            targets_id=targets_latest[0].id if targets_latest else None,
            preferred_scope=getattr(getattr(cfg, "lan", None), "default_scope", ""),
            profiles=profiles,
            wifi_profiles=profiles,
            profile_hashes=profile_hashes,
            selected_profile_evt=selected_profile_evt,
            profiles_error=profiles_error,
        )

    @app.post("/wifi/connect")
    def wifi_connect():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        iface = (request.form.get("iface") or getattr(w, "iface", "wlan0")).strip()

        allow = set(getattr(w, "allow_ssids", []) or [])
        creds = getattr(w, "credentials", None) or {}

        if allow and ssid not in allow:
            abort(403)
        if ssid not in creds:
            abort(400)

        bus.publish("ui.wifi.connect", {"iface": iface, "ssid": ssid})

        return redirect(url_for("wifi"))

    @app.post("/wifi/disconnect")
    def wifi_disconnect():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        if not w:
            abort(400)

        iface = (request.form.get("iface") or getattr(w, "iface", "wlan0")).strip()

        bus.publish("ui.wifi.disconnect", {"iface": iface})
        return redirect(url_for("wifi"))

    @app.post("/wifi/profile/apply")
    def wifi_profile_apply():
        ssid = (request.form.get("ssid") or "").strip()
        iface = (request.form.get("iface") or "").strip()
        bus.publish("ui.wifi.profile.apply", {"ssid": ssid, "iface": iface})
        return redirect(url_for("wifi"))

    @app.post("/wifi/profile/create")
    def wifi_profile_create():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        lan = getattr(cfg, "lan", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        if not ssid or len(ssid) > 128:
            abort(400)

        scope_map = getattr(w, "scope_map", None) or {}
        mapped = (scope_map.get(ssid) or "").strip() if isinstance(scope_map, dict) else ""
        iface = getattr(w, "iface", "wlan0")

        try:
            derived = detect_scope_for_iface(iface) or ""
        except Exception:
            derived = ""

        default_scope = (
            getattr(lan, "default_scope", "10.0.10.0/24") if lan else "10.0.10.0/24"
        )
        scope = mapped or derived or default_scope

        default_pack = getattr(lan, "default_pack", "bjorn_core") if lan else "bjorn_core"
        default_rps = float(getattr(lan, "throttle_rps", 1.0) or 1.0) if lan else 1.0
        default_batch = int(getattr(lan, "batch_size", 4) or 4) if lan else 4

        profile = {
            "scope": scope,
            "disconnect_after_lan": bool(getattr(w, "disconnect_after_lan", True)),
            "lock_during_lan": bool(getattr(w, "lock_during_lan", True)),
            "lan_pack": default_pack,
            "lan_throttle_rps": default_rps,
            "lan_batch_size": default_batch,
        }
        profile_norm, warnings = normalize_profile(profile)
        prof_hash = profile_hash(profile_norm)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_profile_upsert(text, ssid=ssid, profile=profile_norm)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.wifi.profile.normalized",
            {
                "ssid": ssid,
                "warnings": warnings,
                "hash": prof_hash,
                "ts": time.time(),
            },
        )
        bus.publish(
            "ui.wifi.profile.created", {"ssid": ssid, "scope": scope, "ts": time.time()}
        )
        return redirect(url_for("wifi"))

    @app.post("/wifi/profile/preset")
    def wifi_profile_preset():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        lan = getattr(cfg, "lan", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        preset = (request.form.get("preset") or "").strip()
        if not ssid or len(ssid) > 128:
            abort(400)
        if preset not in PRESETS:
            abort(400)

        scope_map = getattr(w, "scope_map", None) or {}
        mapped = (scope_map.get(ssid) or "").strip() if isinstance(scope_map, dict) else ""
        iface = getattr(w, "iface", "wlan0")
        try:
            derived = detect_scope_for_iface(iface) or ""
        except Exception:
            derived = ""

        default_scope = (
            getattr(lan, "default_scope", "10.0.10.0/24") if lan else "10.0.10.0/24"
        )
        scope = mapped or derived or default_scope

        profiles = getattr(w, "profiles", None) or {}
        existing = profiles.get(ssid) if isinstance(profiles, dict) else None
        if not isinstance(existing, dict):
            existing = {}

        prof = dict(existing)
        prof.update(PRESETS[preset])
        prof["scope"] = scope
        prof_norm, warnings = normalize_profile(prof)
        prof_hash = profile_hash(prof_norm)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_profile_upsert(text, ssid=ssid, profile=prof_norm)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.wifi.profile.normalized",
            {
                "ssid": ssid,
                "warnings": warnings,
                "hash": prof_hash,
                "ts": time.time(),
            },
        )
        bus.publish(
            "ui.wifi.profile.preset_applied",
            {"ssid": ssid, "preset": preset, "scope": scope, "ts": time.time()},
        )
        return redirect(url_for("wifi"))

    @app.post("/wifi/credentials/save")
    def wifi_credentials_save():
        body = request.form.get("creds", "")
        creds = parse_wifi_credentials_text(body)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_credentials(text, creds)
        _atomic_write_text(cfg_file, patched)

        bus.publish("ui.wifi.credentials.saved", {"count": len(creds), "ts": time.time()})
        return redirect(url_for("wifi"))

    @app.post("/wifi/credentials/save_reload")
    def wifi_credentials_save_reload():
        body = request.form.get("creds", "")
        creds = parse_wifi_credentials_text(body)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_credentials(text, creds)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.wifi.credentials.saved_reloaded",
            {"count": len(creds), "ts": time.time()},
        )
        return redirect(url_for("wifi"))

    @app.post("/wifi/profiles/save")
    def wifi_profiles_save():
        body = request.form.get("profiles", "")
        prof = parse_wifi_profiles_text(body)
        errs = validate_profiles(prof)
        if errs:
            bus.publish(
                "ui.wifi.profiles.invalid",
                {"errors": errs[:10], "count": len(errs), "ts": time.time()},
            )
            return redirect(url_for("wifi") + "?profiles_error=1")

        norm_profiles = {}
        for ssid, profile in (prof or {}).items():
            norm, warnings = normalize_profile(profile)
            norm_profiles[ssid] = norm
            bus.publish(
                "ui.wifi.profile.normalized",
                {
                    "ssid": ssid,
                    "warnings": warnings,
                    "hash": profile_hash(norm),
                    "ts": time.time(),
                },
            )

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_profiles_set(text, norm_profiles)
        _atomic_write_text(cfg_file, patched)

        bus.publish("ui.wifi.profiles.saved", {"count": len(prof), "ts": time.time()})
        return redirect(url_for("wifi"))

    @app.post("/wifi/profiles/save_reload")
    def wifi_profiles_save_reload():
        body = request.form.get("profiles", "")
        prof = parse_wifi_profiles_text(body)
        errs = validate_profiles(prof)
        if errs:
            bus.publish(
                "ui.wifi.profiles.invalid",
                {"errors": errs[:10], "count": len(errs), "ts": time.time()},
            )
            return redirect(url_for("wifi") + "?profiles_error=1")

        norm_profiles = {}
        for ssid, profile in (prof or {}).items():
            norm, warnings = normalize_profile(profile)
            norm_profiles[ssid] = norm
            bus.publish(
                "ui.wifi.profile.normalized",
                {
                    "ssid": ssid,
                    "warnings": warnings,
                    "hash": profile_hash(norm),
                    "ts": time.time(),
                },
            )

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_profiles_set(text, norm_profiles)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.wifi.profiles.saved_reloaded",
            {"count": len(prof), "ts": time.time()},
        )
        return redirect(url_for("wifi"))

    @app.post("/wifi/allowlist/add")
    def wifi_allowlist_add():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        if not ssid or len(ssid) > 128:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_allow_add(text, ssid=ssid)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish("ui.wifi.allowlist.added", {"ssid": ssid, "ts": time.time()})
        return redirect(url_for("wifi"))

    @app.post("/wifi/allowlist/remove")
    def wifi_allowlist_remove():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        if not ssid or len(ssid) > 128:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_allow_remove(text, ssid=ssid)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish("ui.wifi.allowlist.removed", {"ssid": ssid, "ts": time.time()})
        return redirect(url_for("wifi"))

    @app.post("/wifi/scope_map/set")
    def wifi_scope_map_set():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        scope = (request.form.get("scope") or "").strip()

        if not ssid or len(ssid) > 128:
            abort(400)
        if not scope or len(scope) > 64:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_scope_map_set(text, ssid=ssid, scope=scope)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.wifi.scope_map.set",
            {"ssid": ssid, "scope": scope, "ts": time.time()},
        )
        return redirect(url_for("wifi"))

    @app.post("/wifi/scope_map/remove")
    def wifi_scope_map_remove():
        cfg = store.get()
        w = getattr(cfg, "wifi", None)
        if not w:
            abort(400)

        ssid = (request.form.get("ssid") or "").strip()
        if not ssid or len(ssid) > 128:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_wifi_scope_map_remove(text, ssid=ssid)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish("ui.wifi.scope_map.removed", {"ssid": ssid, "ts": time.time()})
        return redirect(url_for("wifi"))

    @app.get("/lan")
    def lan():
        events = bus.tail(limit=80, topic_prefix="lan.")
        return render_template("lan.html", events=events)

    def _bundle_finding_state(bundle: dict, fid: str):
        """
        Returns:
          None                → finding not present
          "active"            → present, not suppressed
          "suppressed"        → present, suppressed
        """
        hs = bundle.get("host_summary") or {}
        for finding in (hs.get("findings") or []):
            finding_id = str(finding.get("id") or finding.get("title") or "")
            if finding_id != fid:
                continue
            suppressed = bool(
                finding.get("suppressed") or finding.get("suppressed_by_policy")
            )
            return "suppressed" if suppressed else "active"
        return None

    def _bundle_ts(meta: dict, bundle: dict) -> float:
        for key in ("ts", "created_ts", "created_at", "time"):
            value = meta.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        for key in ("ts", "created_ts", "created_at", "time"):
            value = bundle.get(key)
            if isinstance(value, (int, float)):
                return float(value)
        job_id = str(bundle.get("job_id") or "")
        if job_id.startswith("job-"):
            try:
                return float(int(job_id.split("-", 1)[1]))
            except Exception:
                pass
        return 0.0

    def _fmt_ts(ts: float) -> str:
        if not ts:
            return "unknown"
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )

    def _load_profile_timeline(ssid: str | None, limit: int = 50) -> list[dict]:
        if not ssid:
            return []
        metas = artifacts.list(limit=200, kind="profile_timeline")
        rows = []
        for meta in metas:
            payload = artifacts.get_json(meta.id) or {}
            if payload.get("ssid") != ssid:
                continue
            rows.append(
                {
                    "ssid": payload.get("ssid"),
                    "profile_hash": payload.get("profile_hash"),
                    "applied_at": payload.get("applied_at"),
                    "job_id": payload.get("job_id"),
                    "bundle_id": payload.get("bundle_id"),
                    "profile": payload.get("profile") or {},
                }
            )
            if len(rows) >= limit:
                break
        rows.sort(key=lambda x: x.get("applied_at") or 0, reverse=True)
        return rows

    def _expected_findings_for_bundles(bundles: list[dict]) -> set[str]:
        cfg = store.get()
        if bundles:
            return expected_findings_for_bundle(cfg, bundles[0])
        scope = getattr(getattr(cfg, "lan", None), "default_scope", None)
        return expected_findings_for_scope(cfg, scope)

    @app.get("/lan/results")
    def lan_results():
        fid = request.args.get("finding", "").strip()
        include_suppressed = request.args.get("include_suppressed", "0") in (
            "1",
            "true",
            "yes",
        )
        only_suppressed = request.args.get("only_suppressed", "0") in ("1", "true", "yes")

        metas = artifacts.list(limit=50, kind="lan_bundle")
        cfg = store.get()

        bundles = []
        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            bundle.setdefault("id", meta.id)
            bundle.setdefault("title", meta.title)
            bundle.setdefault("diff_summary", bundle.get("diff_summary") or {})
            bundle.setdefault("diff_badges", bundle.get("diff_badges") or {})

            state = None
            if fid:
                state = _bundle_finding_state(bundle, fid)
                if state is None:
                    continue
                if only_suppressed and state != "suppressed":
                    continue
                if not include_suppressed and state == "suppressed":
                    continue

                bundle["_finding_state"] = state
                bundle["_finding_id"] = fid

            try:
                meta_info = (
                    (bundle.get("job") or {}).get("meta") or bundle.get("job_meta") or {}
                )
                bundle["eff"] = effective_lan_overrides(
                    cfg, meta_info if isinstance(meta_info, dict) else {}
                )
            except Exception:
                bundle["eff"] = None

            bundles.append(bundle)

        all_items = (
            bundles
            if not fid
            else [artifacts.get_json(meta.id) or {} for meta in metas]
        )
        expected = _expected_findings_for_bundles(bundles)
        baseline_profile = _profile_key_for_bundle(bundles[0]) if bundles else ""
        top_findings = aggregate_top_findings(
            all_items,
            limit=6,
            expected=expected,
        )
        return render_template(
            "lan_results.html",
            items=bundles,
            top_findings=top_findings,
            finding_filter=fid,
            include_suppressed=include_suppressed,
            only_suppressed=only_suppressed,
            baseline_profile=baseline_profile,
        )

    def _bundle_has_finding(bundle: dict, fid: str):
        summary = bundle.get("host_summary") or {}
        for finding in (summary.get("findings") or []):
            finding_id = str(finding.get("id") or finding.get("title") or "")
            if finding_id != fid:
                continue
            suppressed = bool(
                finding.get("suppressed") or finding.get("suppressed_by_policy")
            )
            return True, suppressed
        return False, False

    def _find_latest_bundle_for_finding(
        fid: str, include_suppressed: bool, only_suppressed: bool
    ) -> str | None:
        metas = artifacts.list(limit=300, kind="lan_bundle")
        best_unsuppressed = None
        best_suppressed = None

        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            ok, suppressed = _bundle_has_finding(bundle, fid)
            if not ok:
                continue

            if suppressed:
                if best_suppressed is None:
                    best_suppressed = meta.id
            else:
                if best_unsuppressed is None:
                    best_unsuppressed = meta.id

            if not only_suppressed and best_unsuppressed is not None:
                break
            if only_suppressed and best_suppressed is not None:
                break

        if only_suppressed:
            return best_suppressed
        if best_unsuppressed:
            return best_unsuppressed
        if include_suppressed:
            return best_suppressed
        return None

    def _load_recent_bundles(limit: int = 50) -> list[dict]:
        metas = artifacts.list(limit=limit, kind="lan_bundle")
        items = []
        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            bundle.setdefault("id", meta.id)
            items.append(bundle)
        return items

    def _pick_scope(cfg, bundles: list[dict]) -> str:
        if bundles:
            scope = (bundles[0].get("scope") or "").strip()
            if scope:
                return scope
        default_scope = (getattr(getattr(cfg, "lan", None), "default_scope", "") or "")
        return default_scope.strip() or "default"

    def _baseline_scopes(cfg) -> list[str]:
        baseline = getattr(cfg, "baseline", None)
        scopes = getattr(baseline, "scopes", None) if baseline else None
        if isinstance(scopes, dict):
            return sorted([str(key) for key in scopes.keys()])
        return []

    def _profile_key_for_bundle(bundle: dict) -> str | None:
        job_meta = (
            (bundle.get("job") or {}).get("meta") if isinstance(bundle.get("job"), dict) else {}
        )
        if not job_meta and isinstance(bundle.get("job_meta"), dict):
            job_meta = bundle.get("job_meta") or {}
        return profile_key_for_job_meta(job_meta)

    def _baseline_profiles(cfg) -> list[str]:
        baseline = getattr(cfg, "baseline", None)
        profiles = getattr(baseline, "profiles", None) if baseline else None
        if isinstance(profiles, dict):
            return sorted([str(key) for key in profiles.keys()])
        return []

    def _pick_profile(cfg, bundles: list[dict]) -> str:
        if bundles:
            key = _profile_key_for_bundle(bundles[0]) or ""
            if key:
                return key
        profiles = _baseline_profiles(cfg)
        return profiles[0] if profiles else ""

    @app.get("/lan/baseline")
    def lan_baseline_overview():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=200)
        scopes = _baseline_scopes(cfg)
        profiles = _baseline_profiles(cfg)
        profile_q = (request.args.get("profile") or "").strip()
        scope_q = (request.args.get("scope") or "").strip()
        profile = profile_q or _pick_profile(cfg, bundles)
        if profiles and profile not in profiles:
            profile = profiles[0]
        scope = scope_q or _pick_scope(cfg, bundles)
        if scopes and scope not in scopes:
            scope = scopes[0]
        expected = (
            expected_findings_for_profile(cfg, profile)
            if profile
            else expected_findings_for_scope(cfg, scope)
        )

        window = int(request.args.get("window", "50") or "50")
        window = max(5, min(window, 500))
        window_bundles = [
            b for b in bundles if not profile or _profile_key_for_bundle(b) == profile
        ][:window]

        diff = compute_baseline_diff(profile or scope, expected, window_bundles)

        return render_template(
            "lan_baseline.html",
            scope=scope,
            profile=profile,
            scopes=scopes,
            profiles=profiles,
            window=window,
            expected_count=len(expected),
            diff=diff,
        )

    @app.get("/lan/baseline/diff")
    def lan_baseline_diff_latest():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=50)
        scopes = _baseline_scopes(cfg)
        profiles = _baseline_profiles(cfg)
        profile_q = (request.args.get("profile") or "").strip()
        scope_q = (request.args.get("scope") or "").strip()
        profile = profile_q or _pick_profile(cfg, bundles)
        if profiles and profile not in profiles:
            profile = profiles[0]
        scope = scope_q or _pick_scope(cfg, bundles)
        if scopes and scope not in scopes:
            scope = scopes[0]
        expected = (
            expected_findings_for_profile(cfg, profile)
            if profile
            else expected_findings_for_scope(cfg, scope)
        )

        filtered = [
            b for b in bundles if not profile or _profile_key_for_bundle(b) == profile
        ]
        latest = filtered[0] if filtered else {}
        diff = compute_baseline_diff(profile or scope, expected, [latest] if latest else [])

        return render_template(
            "lan_baseline_diff.html",
            scope=scope,
            profile=profile,
            scopes=scopes,
            profiles=profiles,
            bundle_id=(latest.get("id") if latest else None),
            diff=diff,
        )

    @app.post("/lan/baseline/add")
    def lan_baseline_add():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=50)
        scope = (request.form.get("scope") or "").strip() or _pick_scope(cfg, bundles)
        profile = (request.form.get("profile") or "").strip() or _pick_profile(cfg, bundles)
        fid = (request.form.get("fid") or "").strip()

        if not fid or "\n" in fid or "\r" in fid or len(fid) > 200:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        if profile:
            patched = patch_baseline_profile_add(text, profile_key=profile, finding_id=fid)
            patched = cleanup_baseline_profiles(patched)
        else:
            patched = patch_baseline_add(text, scope=scope, finding_id=fid)
            patched = cleanup_baseline_scopes(patched)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.baseline.added",
            {"scope": scope, "profile": profile, "fid": fid, "ts": time.time()},
        )

        back = request.form.get("back") or ""
        if back:
            return redirect(back)
        return redirect(url_for("lan_baseline_overview"))

    @app.post("/lan/baseline/remove")
    def lan_baseline_remove():
        cfg = store.get()
        bundles = _load_recent_bundles(limit=50)
        scope = (request.form.get("scope") or "").strip() or _pick_scope(cfg, bundles)
        profile = (request.form.get("profile") or "").strip() or _pick_profile(cfg, bundles)
        fid = (request.form.get("fid") or "").strip()

        if not fid or "\n" in fid or "\r" in fid or len(fid) > 200:
            abort(400)

        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        if profile:
            patched = patch_baseline_profile_remove(text, profile_key=profile, finding_id=fid)
            patched = cleanup_baseline_profiles(patched)
        else:
            patched = patch_baseline_remove(text, scope=scope, finding_id=fid)
            patched = cleanup_baseline_scopes(patched)
        _atomic_write_text(cfg_file, patched)

        store.reload()
        bus.publish(
            "ui.baseline.removed",
            {"scope": scope, "profile": profile, "fid": fid, "ts": time.time()},
        )

        back = request.form.get("back") or ""
        return redirect(back or url_for("lan_baseline_overview"))

    @app.post("/lan/baseline/cleanup")
    def lan_baseline_cleanup():
        cfg_file = Path(config_path)
        text = cfg_file.read_text(encoding="utf-8")
        patched = cleanup_baseline_scopes(text)
        patched = cleanup_baseline_profiles(patched)
        _atomic_write_text(cfg_file, patched)
        store.reload()
        bus.publish("ui.baseline.cleaned", {"ts": time.time()})
        return redirect(url_for("lan_baseline_overview"))

    @app.get("/lan/finding/<fid>/jump")
    def lan_finding_jump(fid: str):
        fid = fid.strip()
        if not fid:
            abort(400)
        include_suppressed = request.args.get("include_suppressed", "0") in (
            "1",
            "true",
            "yes",
        )
        only_suppressed = request.args.get("only_suppressed", "0") in (
            "1",
            "true",
            "yes",
        )
        bundle_id = _find_latest_bundle_for_finding(
            fid,
            include_suppressed=include_suppressed,
            only_suppressed=only_suppressed,
        )
        if not bundle_id:
            return redirect(url_for("lan_results") + f"?finding={fid}")
        return redirect(url_for("lan_result_details", bundle_id=bundle_id))

    @app.get("/lan/summary")
    def lan_exec_summary():
        bundles = _load_recent_bundles(limit=50)
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            bundles, limit=10, expected=expected
        )
        summary = build_exec_summary(bundles, top_findings)
        html = render_exec_summary_html(summary)
        return Response(html, mimetype="text/html")

    @app.get("/lan/summary.md")
    def lan_exec_summary_md():
        bundles = _load_recent_bundles(limit=50)
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            bundles, limit=10, expected=expected
        )
        summary = build_exec_summary(bundles, top_findings)
        md = render_exec_summary_md(summary)
        return Response(md, mimetype="text/markdown; charset=utf-8")

    @app.get("/lan/summary.json")
    def lan_exec_summary_json():
        bundles = _load_recent_bundles(limit=50)
        expected = _expected_findings_for_bundles(bundles)
        top_findings = aggregate_top_findings(
            bundles, limit=10, expected=expected
        )
        summary = build_exec_summary(bundles, top_findings)
        return Response(
            response=json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
            status=200,
            mimetype="application/json",
            headers={
                "Content-Disposition": 'attachment; filename="smolotchi_lan_summary.json"'
            },
        )

    def resolve_result_by_job_id(job_id: str):
        """
        Fallback resolver:
        1) Try lan_bundle by job_id (fast)
        2) Else: scan artifacts index for lan_result/lan_report and correlate via content.job.id
        """
        bundle_id = artifacts.find_bundle_by_job_id(job_id)
        if bundle_id:
            bundle = artifacts.get_json(bundle_id)
            json_id = (bundle.get("result_json") or {}).get("artifact_id")
            reports = bundle.get("reports") or {}
            report_html = reports.get("html") or bundle.get("report_html") or {}
            report_md = reports.get("md") or {}
            report_json = reports.get("json") or {}
            rep_id = report_html.get("artifact_id")
            diff_report = reports.get("diff") or {}
            diff_summary = bundle.get("diff_summary") or {}
            diff_badges = bundle.get("diff_badges") or {}
            return {
                "bundle_id": bundle_id,
                "bundle": bundle,
                "json_id": json_id,
                "report_id": rep_id,
                "report_md_id": report_md.get("artifact_id"),
                "report_json_id": report_json.get("artifact_id"),
                "diff_html_id": (diff_report.get("html") or {}).get("artifact_id"),
                "diff_md_id": (diff_report.get("md") or {}).get("artifact_id"),
                "diff_json_id": (diff_report.get("json") or {}).get("artifact_id")
                or diff_summary.get("artifact_id"),
                "diff_changed_hosts": diff_summary.get("changed_hosts", []),
                "diff_changed_hosts_count": diff_summary.get("changed_hosts_count"),
                "diff_badges": diff_badges,
            }

        idx = artifacts.list(limit=300)
        json_id = None
        report_id = None

        for artifact in idx:
            if artifact.kind == "lan_result":
                data = artifacts.get_json(artifact.id)
                if data and str(data.get("job", {}).get("id")) == job_id:
                    json_id = artifact.id
                    break

        for artifact in idx:
            if artifact.kind == "lan_report" and job_id in artifact.title:
                report_id = artifact.id
                break

        return {
            "bundle_id": None,
            "bundle": None,
            "json_id": json_id,
            "report_id": report_id,
            "report_md_id": None,
            "report_json_id": None,
            "diff_html_id": None,
            "diff_md_id": None,
            "diff_json_id": None,
            "diff_changed_hosts": [],
            "diff_changed_hosts_count": None,
            "diff_badges": {},
        }

    @app.get("/lan/result/<bundle_id>")
    def lan_result_details(bundle_id: str):
        bundle = artifacts.get_json(bundle_id)
        if not bundle:
            abort(404)
        json_id = (bundle.get("result_json") or {}).get("artifact_id")
        reports = bundle.get("reports") or {}
        report = reports.get("html") or bundle.get("report_html") or {}
        report_md = reports.get("md") or {}
        report_json = reports.get("json") or {}
        report_id = report.get("artifact_id")
        diff_report = reports.get("diff") or {}
        diff_summary = bundle.get("diff_summary") or {}
        diff_badges = bundle.get("diff_badges") or {}
        resolved = {
            "bundle_id": bundle_id,
            "bundle": bundle,
            "json_id": json_id,
            "report_id": report_id,
            "report_md_id": report_md.get("artifact_id"),
            "report_json_id": report_json.get("artifact_id"),
            "diff_html_id": (diff_report.get("html") or {}).get("artifact_id"),
            "diff_md_id": (diff_report.get("md") or {}).get("artifact_id"),
            "diff_json_id": (diff_report.get("json") or {}).get("artifact_id")
            or diff_summary.get("artifact_id"),
            "diff_changed_hosts": diff_summary.get("changed_hosts", []),
            "diff_changed_hosts_count": diff_summary.get("changed_hosts_count"),
            "diff_badges": diff_badges,
        }
        return _render_result_details(resolved, job_id=bundle.get("job_id"))

    @app.get("/lan/result")
    def lan_result_by_job():
        job_id = request.args.get("job_id", "").strip()
        if not job_id:
            abort(400)
        resolved = resolve_result_by_job_id(job_id)
        return _render_result_details(resolved, job_id=job_id)

    @app.get("/lan/finding/<fid>/timeline")
    def lan_finding_timeline(fid: str):
        fid = fid.strip()
        if not fid:
            abort(400)

        metas = artifacts.list(limit=500, kind="lan_bundle")
        history = []
        for meta in metas:
            bundle = artifacts.get_json(meta.id) or {}
            state = _bundle_finding_state(bundle, fid)
            if state is None:
                continue
            meta_data = artifacts.get_meta(meta.id) or {}
            ts = _bundle_ts(meta_data, bundle)
            history.append(
                {
                    "ts": ts,
                    "ts_str": _fmt_ts(ts),
                    "bundle_id": meta.id,
                    "state": state,
                }
            )

        if not history:
            return render_template(
                "lan_finding_timeline.html",
                fid=fid,
                first=None,
                last=None,
                history=[],
            )

        history_sorted = sorted(history, key=lambda x: x["ts"] or 0)
        first = history_sorted[0]
        last = history_sorted[-1]
        history_desc = sorted(history_sorted, key=lambda x: x["ts"] or 0, reverse=True)

        return render_template(
            "lan_finding_timeline.html",
            fid=fid,
            first=first,
            last=last,
            history=history_desc,
        )

    def _render_result_details(resolved: dict, job_id: str | None):
        bundle_id = resolved.get("bundle_id")
        bundle = resolved.get("bundle")
        json_id = resolved.get("json_id")
        report_id = resolved.get("report_id")
        report_md_id = resolved.get("report_md_id")
        report_json_id = resolved.get("report_json_id")
        diff_html_id = resolved.get("diff_html_id")
        diff_md_id = resolved.get("diff_md_id")
        diff_json_id = resolved.get("diff_json_id")
        diff_changed_hosts = resolved.get("diff_changed_hosts") or []
        diff_changed_hosts_count = resolved.get("diff_changed_hosts_count")
        diff_badges = resolved.get("diff_badges") or {}
        if diff_changed_hosts_count is None and diff_changed_hosts:
            diff_changed_hosts_count = len(diff_changed_hosts)

        result_json = artifacts.get_json(json_id) if json_id else None
        bundle_pretty = pretty(bundle) if bundle else ""
        result_pretty = pretty(result_json) if result_json else ""
        job_meta = None
        if result_json and isinstance(result_json, dict):
            job_meta = (result_json.get("job") or {}).get("meta")
        if not job_meta and bundle and isinstance(bundle, dict):
            job_meta = (bundle.get("job") or {}).get("meta") or bundle.get("job_meta")

        eff = effective_lan_overrides(
            store.get(), job_meta if isinstance(job_meta, dict) else {}
        )
        if eff.get("profile_drift"):
            bus.publish(
                "lan.profile.drift_detected",
                {
                    "job_id": job_id,
                    "ssid": eff.get("wifi_ssid"),
                    "applied_hash": eff.get("profile_hash"),
                    "current_hash": eff.get("profile_current_hash"),
                    "ts": time.time(),
                },
            )

        profile_timeline = _load_profile_timeline(eff.get("wifi_ssid"))

        evts = []
        if job_id:
            raw = bus.tail(limit=300)
            for event in raw:
                payload = event.payload or {}
                if payload.get("id") == job_id or payload.get("job", {}).get("id") == job_id:
                    evts.append(event)
            evts = evts[:80]

        return render_template(
            "lan_result_details_tabs.html",
            job_id=job_id,
            bundle_id=bundle_id,
            bundle_pretty=bundle_pretty,
            result_json_id=json_id,
            result_pretty=result_pretty,
            report_id=report_id,
            report_md_id=report_md_id,
            report_json_id=report_json_id,
            diff_html_id=diff_html_id,
            diff_md_id=diff_md_id,
            diff_json_id=diff_json_id,
            diff_changed_hosts=diff_changed_hosts,
            diff_changed_hosts_count=diff_changed_hosts_count,
            diff_badges=diff_badges,
            events=evts,
            job_meta=job_meta,
            eff=eff,
            profile_timeline=profile_timeline,
        )

    @app.get("/lan/reports")
    def lan_reports():
        report_metas = artifacts.list(limit=50, kind="lan_report")

        bundle_metas = artifacts.list(limit=200, kind="lan_bundle")
        report_to_bundle: dict[str, str] = {}
        bundle_cache: dict[str, dict] = {}

        for bm in bundle_metas:
            bundle = artifacts.get_json(bm.id) or {}
            bundle_cache[bm.id] = bundle
            reports = bundle.get("reports") or {}
            html = reports.get("html") or bundle.get("report_html") or {}
            rep_id = (html or {}).get("artifact_id")
            if rep_id:
                report_to_bundle[str(rep_id)] = bm.id

        items = []
        for rm in report_metas:
            bundle_id = report_to_bundle.get(rm.id)
            job_id = None
            diff_html_id = None
            diff_md_id = None
            diff_json_id = None

            if bundle_id:
                bundle = bundle_cache.get(bundle_id) or (artifacts.get_json(bundle_id) or {})
                job_id = bundle.get("job_id")

                reports = bundle.get("reports") or {}
                diff_report = reports.get("diff") or {}
                diff_summary = bundle.get("diff_summary") or {}

                diff_html_id = (diff_report.get("html") or {}).get("artifact_id")
                diff_md_id = (diff_report.get("md") or {}).get("artifact_id")
                diff_json_id = (diff_report.get("json") or {}).get("artifact_id") or diff_summary.get(
                    "artifact_id"
                )

            items.append(
                {
                    "id": rm.id,
                    "title": rm.title,
                    "bundle_id": bundle_id,
                    "job_id": job_id,
                    "diff_html_id": diff_html_id,
                    "diff_md_id": diff_md_id,
                    "diff_json_id": diff_json_id,
                }
            )

        return render_template("lan_reports.html", items=items)

    def _resolve_bundle(bundle_id: str):
        bundle = artifacts.get_json(bundle_id)
        if bundle:
            return bundle_id, bundle
        bundle_id = artifacts.find_bundle_by_job_id(bundle_id)
        if not bundle_id:
            return None, None
        return bundle_id, artifacts.get_json(bundle_id)

    @app.get("/lan/diff/host/<bundle_id>/<host>")
    def lan_host_diff(bundle_id: str, host: str):
        bundle_id, bundle = _resolve_bundle(bundle_id)
        if not bundle:
            abort(404)
        reports = bundle.get("reports") or {}
        diff_report = reports.get("diff") or {}
        diff_summary = bundle.get("diff_summary") or {}
        diff_json_id = (diff_report.get("json") or {}).get("artifact_id") or diff_summary.get(
            "artifact_id"
        )
        if not diff_json_id:
            abort(404)
        diff = artifacts.get_json(diff_json_id) or {}
        prev_v = request.args.get("prev_v", "").strip()
        cur_v = request.args.get("cur_v", "").strip()
        html = host_diff_html(diff, host, artifacts=artifacts, prev_v=prev_v, cur_v=cur_v)
        return Response(html, mimetype="text/html")

    @app.get("/lan/diff/host/<bundle_id>/<host>.md")
    def lan_host_diff_md(bundle_id: str, host: str):
        bundle_id, bundle = _resolve_bundle(bundle_id)
        if not bundle:
            abort(404)
        reports = bundle.get("reports") or {}
        diff_report = reports.get("diff") or {}
        diff_summary = bundle.get("diff_summary") or {}
        diff_json_id = (diff_report.get("json") or {}).get("artifact_id") or diff_summary.get(
            "artifact_id"
        )
        if not diff_json_id:
            abort(404)
        diff = artifacts.get_json(diff_json_id) or {}
        md = host_diff_markdown(diff, host)
        return Response(md, mimetype="text/markdown; charset=utf-8")

    @app.get("/artifact/<artifact_id>")
    def artifact_view(artifact_id: str):
        data = artifacts.get_json(artifact_id)
        if data is None:
            abort(404)
        return render_template("artifact.html", artifact_id=artifact_id, data=data)

    @app.get("/artifact/<artifact_id>.json")
    def artifact_download(artifact_id: str):
        data = artifacts.get_json(artifact_id)
        if data is None:
            abort(404)
        return Response(
            response=json.dumps(data, ensure_ascii=False, indent=2),
            status=200,
            mimetype="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{artifact_id}.json"'
            },
        )

    @app.get("/artifact/<artifact_id>/download")
    def artifact_file_download(artifact_id: str):
        meta = artifacts.get_meta(artifact_id)
        if not meta:
            abort(404)
        path = _safe_store_path(artifacts.root, meta.get("path"))
        return send_file(
            path,
            as_attachment=True,
            download_name=meta.get("name") or path.name,
        )

    @app.get("/report/<artifact_id>")
    def report_view(artifact_id: str):
        meta = artifacts.get_meta(artifact_id)
        if not meta:
            abort(404)
        path = _safe_store_path(artifacts.root, meta.get("path"))
        if path.suffix.lower() not in {".html", ".md", ".json"}:
            abort(404)
        return send_file(path, as_attachment=False)

    @app.get("/lan/jobs")
    def lan_jobs():
        queued = jobstore.list(limit=30, status="queued")
        running = jobstore.list(limit=10, status="running")
        done = jobstore.list(limit=30, status="done")
        failed = jobstore.list(limit=30, status="failed")

        def _enrich_jobs(jobs):
            cfg = store.get()
            lan = getattr(cfg, "lan", None)

            default_pack = (
                getattr(lan, "default_pack", "bjorn_core") if lan else "bjorn_core"
            )
            default_rps = float(getattr(lan, "throttle_rps", 1.0) or 1.0) if lan else 1.0
            default_batch = int(getattr(lan, "batch_size", 4) or 4) if lan else 4

            for j in jobs:
                meta = getattr(j, "meta", None) or {}
                if not isinstance(meta, dict):
                    meta = {}

                over = meta.get("lan_overrides") or {}
                if not isinstance(over, dict):
                    over = {}

                j.eff_pack = over.get("pack") or default_pack
                j.eff_throttle_rps = (
                    over.get("throttle_rps")
                    if over.get("throttle_rps") is not None
                    else default_rps
                )
                j.eff_batch_size = (
                    over.get("batch_size")
                    if over.get("batch_size") is not None
                    else default_batch
                )

                j.wifi_ssid = (meta.get("wifi_ssid") or "")
                j.wifi_iface = (meta.get("wifi_iface") or "")
            return jobs

        queued = _enrich_jobs(queued)
        running = _enrich_jobs(running)
        done = _enrich_jobs(done)
        failed = _enrich_jobs(failed)
        links = artifacts.list(limit=200, kind="ai_job_link")
        run_by_job = {}
        for link in links:
            doc = artifacts.get_json(link.id) or {}
            jid = doc.get("job_id")
            rid = doc.get("run_artifact_id")
            if jid and rid:
                run_by_job[str(jid)] = str(rid)
        return render_template(
            "lan_jobs.html",
            queued=queued,
            running=running,
            done=done,
            failed=failed,
            run_by_job=run_by_job,
        )

    @app.post("/lan/job/<job_id>/cancel")
    def lan_job_cancel(job_id: str):
        ok = jobstore.cancel(job_id)
        bus.publish("ui.job.cancel", {"id": job_id, "ok": ok})
        return redirect(url_for("lan_jobs"))

    @app.post("/lan/job/<job_id>/reset")
    def lan_job_reset(job_id: str):
        ok = jobstore.reset_running(job_id)
        bus.publish("ui.job.reset", {"id": job_id, "ok": ok})
        return redirect(url_for("lan_jobs"))

    @app.post("/lan/job/<job_id>/delete")
    def lan_job_delete(job_id: str):
        ok = jobstore.delete(job_id)
        bus.publish("ui.job.delete", {"id": job_id, "ok": ok})
        return redirect(url_for("lan_jobs"))

    @app.get("/lan/policy")
    def lan_policy():
        cfg_file = Path(config_path)
        cfg = store.get()
        noisy = getattr(getattr(cfg, "lan", None), "noisy_scripts", None) or []
        allow = getattr(getattr(cfg, "lan", None), "allowlist_scripts", None) or []
        return render_template(
            "lan_policy.html",
            noisy="\n".join(noisy),
            allow="\n".join(allow),
        )

    @app.post("/lan/policy")
    def lan_policy_save():
        cfg_file = Path(config_path)
        noisy = [
            value.strip()
            for value in request.form.get("noisy", "").splitlines()
            if value.strip()
        ]
        allow = [
            value.strip()
            for value in request.form.get("allow", "").splitlines()
            if value.strip()
        ]
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_lan_lists(text, noisy=noisy, allow=allow)
        _atomic_write_text(cfg_file, patched)
        bus.publish("ui.policy.saved", {"ts": time.time()})
        return redirect(url_for("lan_policy"))

    @app.post("/lan/policy/save_reload")
    def lan_policy_save_reload():
        cfg_file = Path(config_path)
        noisy = [
            value.strip()
            for value in request.form.get("noisy", "").splitlines()
            if value.strip()
        ]
        allow = [
            value.strip()
            for value in request.form.get("allow", "").splitlines()
            if value.strip()
        ]
        text = cfg_file.read_text(encoding="utf-8")
        patched = patch_lan_lists(text, noisy=noisy, allow=allow)
        _atomic_write_text(cfg_file, patched)
        store.reload()
        bus.publish("ui.policy.saved_reloaded", {"ts": time.time()})
        return redirect(url_for("lan_policy"))

    @app.get("/config")
    def config():
        cfg = store.get()
        cfg_file = Path(config_path)
        msg = None
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception as exc:
            content = ""
            msg = {"title": "Error", "text": f"Failed to read {cfg_file}: {exc}"}

        return render_template(
            "config.html",
            cfg=cfg,
            config_path=str(cfg_file),
            content=content,
            msg=msg,
        )

    @app.post("/config")
    def config_save():
        cfg_file = Path(config_path)
        content = request.form.get("content", "")
        msg = None

        try:
            if not isinstance(content, str):
                raise ValueError("Invalid content")
            _atomic_write_text(cfg_file, content)
            msg = {
                "title": "Saved",
                "text": f"Updated {cfg_file}. You may want to Reload config.",
            }
            bus.publish("ui.config.saved", {"path": str(cfg_file), "ts": time.time()})
        except Exception as exc:
            msg = {"title": "Error", "text": f"Failed to write {cfg_file}: {exc}"}

        cfg = store.get()
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception:
            pass

        return render_template(
            "config.html",
            cfg=cfg,
            config_path=str(cfg_file),
            content=content,
            msg=msg,
        )

    @app.post("/config/save_reload")
    def config_save_reload():
        cfg_file = Path(config_path)
        content = request.form.get("content", "")
        msg = None

        try:
            if not isinstance(content, str):
                raise ValueError("Invalid content")

            _atomic_write_text(cfg_file, content)
            store.reload()

            bus.publish(
                "ui.config.saved_reloaded",
                {"path": str(cfg_file), "ts": time.time()},
            )

            msg = {
                "title": "Saved & Reloaded",
                "text": f"{cfg_file} updated and reloaded successfully.",
            }
        except Exception as exc:
            msg = {"title": "Error", "text": f"Save+Reload failed: {exc}"}

        cfg = store.get()
        try:
            content = cfg_file.read_text(encoding="utf-8")
        except Exception:
            pass

        return render_template(
            "config.html",
            cfg=cfg,
            config_path=str(cfg_file),
            content=content,
            msg=msg,
        )

    @app.post("/config/reload")
    def config_reload():
        store.reload()
        bus.publish("ui.config.reloaded", {"path": config_path, "ts": time.time()})
        return redirect(url_for("config"))

    @app.get("/audit")
    def audit():
        events = bus.tail(limit=120)
        return render_template("audit.html", events=events)

    @app.post("/handoff")
    def handoff():
        tag = request.form.get("tag", "lab-approved")
        note = request.form.get("note", "")
        bus.publish("ui.handoff.request", {"tag": tag, "note": note})
        return redirect(url_for("dashboard"))

    @app.post("/lan_done")
    def lan_done():
        bus.publish("lan.done", {"note": "manual done"})
        return redirect(url_for("lan"))

    @app.post("/lan_enqueue")
    def lan_enqueue():
        scope = request.form.get("scope", "10.0.10.0/24")
        note = request.form.get("note", "")
        bus.publish(
            "ui.lan.enqueue",
            {
                "job": {
                    "id": f"job-{int(time.time())}",
                    "kind": "inventory",
                    "scope": scope,
                    "note": note,
                }
            },
        )
        return redirect(url_for("lan"))

    @app.get("/ai/plans")
    def ai_plans():
        plan_metas = artifacts.list(limit=50, kind="ai_plan")
        run_metas = artifacts.list(limit=50, kind="ai_plan_run")

        runs_by_plan = {}
        for run in run_metas:
            meta = artifacts.get_meta(run.id) or {}
            plan_id = meta.get("plan_id")
            if plan_id:
                runs_by_plan.setdefault(plan_id, []).append(run)

        plans = []
        for meta in plan_metas:
            data = artifacts.get_json(meta.id) or {}
            plan_id = data.get("id") or meta.id
            plans.append({"meta": meta, "data": data, "plan_id": plan_id})

        return render_template(
            "ai_plans.html",
            plans=plans,
            runs_by_plan=runs_by_plan,
        )

    @app.get("/ai/plan/<artifact_id>")
    def ai_plan_detail(artifact_id: str):
        plan = artifacts.get_json(artifact_id)
        if not plan:
            abort(404)

        plan_id = plan.get("id") or artifact_id
        run_metas = artifacts.list(limit=20, kind="ai_plan_run")
        related_runs = []
        for run in run_metas:
            meta = artifacts.get_meta(run.id) or {}
            if meta.get("plan_id") == plan_id:
                related_runs.append(run)

        return render_template(
            "ai_plan_detail.html",
            plan=plan,
            plan_artifact_id=artifact_id,
            runs=related_runs,
            plan_pretty=pretty(plan),
        )

    @app.get("/ai/run/<artifact_id>")
    def ai_run_detail(artifact_id: str):
        run = artifacts.get_json(artifact_id)
        if not run:
            abort(404)

        # ---- normalize per-step links so template can render safely
        steps = run.get("steps") or []
        if not isinstance(steps, list):
            steps = []

        def normalize_links(raw) -> dict:
            links = raw if isinstance(raw, dict) else {}
            out = {}
            for key in ("artifacts", "reports", "bundles", "jobs"):
                value = links.get(key)
                if not value:
                    out[key] = []
                elif isinstance(value, list):
                    out[key] = [str(item) for item in value if item]
                else:
                    out[key] = [str(value)]
                out[key] = sorted(set(out[key]))
            return out

        for step in steps:
            if not isinstance(step, dict):
                continue
            step["links"] = normalize_links(step.get("links"))

        # ---- aggregate run-level links from steps (for the top "Links" section)
        run_links = {
            "artifacts": set(),
            "reports": set(),
            "bundles": set(),
            "jobs": set(),
        }
        for step in steps:
            if not isinstance(step, dict):
                continue
            links = normalize_links(step.get("links"))
            for key in ("artifacts", "reports", "bundles", "jobs"):
                vals = links.get(key) or []
                for value in vals:
                    if value:
                        run_links[key].add(str(value))

        links = {
            "artifacts": sorted(run_links["artifacts"]),
            "reports": sorted(run_links["reports"]),
            "bundles": sorted(run_links["bundles"]),
            "jobs": sorted(run_links["jobs"]),
        }

        # ---- resolve plan_artifact_id (so "Open Plan" button works)
        plan_artifact_id = None
        plan_id = run.get("plan_id")
        if plan_id:
            plans = artifacts.list(limit=100, kind="ai_plan")
            for plan_meta in plans:
                doc = artifacts.get_json(plan_meta.id) or {}
                if doc.get("id") == plan_id:
                    plan_artifact_id = plan_meta.id
                    break

        # ---- render
        return render_template(
            "ai_run_detail.html",
            run=run,
            run_artifact_id=artifact_id,
            plan_artifact_id=plan_artifact_id,
            run_pretty=pretty(run),
            links=links,
        )

    @app.post("/ai/plan")
    def ai_plan():
        scope = request.form.get("scope", "10.0.10.0/24")
        note = request.form.get("note", "")
        bus.publish("ui.ai.generate_plan", {"scope": scope, "note": note})
        if not core_recently_active()[0]:
            planner = AIPlanner(bus=bus, registry=registry, artifacts=artifacts)
            planner.generate(
                scope=scope,
                mode="autonomous_safe",
                note=note,
            )
        return redirect(url_for("dashboard"))

    @app.post("/ai/run")
    def ai_run():
        plan_artifact_id = (request.form.get("plan_artifact_id") or "").strip()
        scope = (request.form.get("scope") or "").strip()
        note = request.form.get("note") or ""

        req = {
            "plan_artifact_id": plan_artifact_id or None,
            "scope": scope or None,
            "note": note,
            "ts": time.time(),
        }
        req_meta = artifacts.put_json(
            kind="ai_run_request",
            title=f"AI Run Request {int(time.time())}",
            payload=req,
            tags=["ai", "run_request"],
        )
        req_id = req_meta.id

        job_id = f"ai-{int(time.time())}"
        jobstore.enqueue(
            {
                "id": job_id,
                "kind": "ai_plan",
                "scope": scope or "auto",
                "note": f"req:{req_id} {note}".strip(),
            },
        )
        bus.publish(
            "ui.ai.enqueued",
            {"job_id": job_id, "req_id": req_id, "ts": time.time()},
        )
        return redirect(url_for("ai_jobs"))

    @app.get("/ai/jobs")
    def ai_jobs():
        queued = [
            j for j in jobstore.list(limit=30, status="queued") if j.kind == "ai_plan"
        ]
        running = [
            j for j in jobstore.list(limit=10, status="running") if j.kind == "ai_plan"
        ]
        blocked = [
            j for j in jobstore.list(limit=30, status="blocked") if j.kind == "ai_plan"
        ]
        done = [
            j for j in jobstore.list(limit=30, status="done") if j.kind == "ai_plan"
        ]
        failed = [
            j for j in jobstore.list(limit=30, status="failed") if j.kind == "ai_plan"
        ]

        links = artifacts.list(limit=200, kind="ai_job_link")
        run_by_job = {}
        for link in links:
            doc = artifacts.get_json(link.id) or {}
            jid = doc.get("job_id")
            rid = doc.get("run_artifact_id")
            if jid and rid:
                run_by_job[str(jid)] = str(rid)

        return render_template(
            "ai_jobs.html",
            queued=queued,
            running=running,
            blocked=blocked,
            done=done,
            failed=failed,
            run_by_job=run_by_job,
        )

    @app.get("/ai/stages")
    def ai_stages():
        reqs = artifacts.list(limit=50, kind="ai_stage_request")
        approvals = artifacts.list(limit=200, kind="ai_stage_approval")

        approved = set()
        for a in approvals:
            doc = artifacts.get_json(a.id) or {}
            rid = doc.get("request_id")
            if rid:
                approved.add(str(rid))

        cfg = store.get()
        caps = getattr(getattr(cfg, "policy", None), "capabilities", None)
        intrusive_ok = bool(getattr(caps, "intrusive", False)) if caps else False
        dangerous_ok = bool(getattr(caps, "dangerous", False)) if caps else False

        return render_template(
            "ai_stages.html",
            reqs=reqs,
            approved=approved,
            intrusive_ok=intrusive_ok,
            dangerous_ok=dangerous_ok,
        )

    @app.get("/ai/stage/new")
    def ai_stage_new():
        cfg = store.get()
        caps = getattr(getattr(cfg, "policy", None), "capabilities", None)
        intrusive_ok = bool(getattr(caps, "intrusive", False)) if caps else False
        dangerous_ok = bool(getattr(caps, "dangerous", False)) if caps else False
        return render_template(
            "ai_stage_new.html",
            intrusive_ok=intrusive_ok,
            dangerous_ok=dangerous_ok,
        )

    @app.post("/ai/stage/new")
    def ai_stage_new_post():
        plan_artifact_id = (request.form.get("plan_artifact_id") or "").strip()
        stage = (request.form.get("stage") or "exploit").strip()
        target = (request.form.get("target") or "").strip()
        exploit = (request.form.get("exploit") or "").strip()
        risk = (request.form.get("risk") or "intrusive").strip()

        req_payload = {
            "plan_artifact_id": plan_artifact_id,
            "stage": stage,
            "target": target,
            "exploit": exploit,
            "risk": risk,
            "ts": time.time(),
        }
        req_meta = artifacts.put_json(
            kind="ai_stage_request",
            title=f"AI Stage Request {stage} {target or 'n/a'}",
            payload=req_payload,
            tags=["ai", "stage", "request", risk],
            meta={"risk": risk, "stage": stage},
        )

        bus.publish("ui.ai.stage.requested", {"request_id": req_meta.id, "ts": time.time()})
        return redirect(url_for("ai_stages"))

    @app.post("/ai/stage/<request_id>/approve")
    def ai_stage_approve(request_id: str):
        existing_approvals = artifacts.list(limit=200, kind="ai_stage_approval")
        for approval in existing_approvals:
            doc = artifacts.get_json(approval.id) or {}
            if str(doc.get("request_id")) == str(request_id):
                return redirect(url_for("ai_stages"))
        stage_req = artifacts.get_json(request_id) or {}
        appr_payload = {
            "request_id": request_id,
            "approved_by": "local-ui",
            "ts": time.time(),
        }
        appr_meta = artifacts.put_json(
            kind="ai_stage_approval",
            title=f"AI Stage Approval {request_id}",
            payload=appr_payload,
            tags=["ai", "stage", "approval"],
            meta={"request_id": request_id},
        )
        job_id = stage_req.get("job_id")
        step_index = stage_req.get("step_index")
        if job_id and step_index is not None:
            try:
                note = (
                    f"approval granted resume_from:{int(step_index)} "
                    f"stage_req:{request_id}"
                )
                jobstore.mark_queued(str(job_id), note=note)
            except Exception:
                pass
        bus.publish(
            "ui.ai.stage.approved",
            {"approval_id": appr_meta.id, "request_id": request_id, "ts": time.time()},
        )
        return redirect(url_for("ai_stages"))

    @app.post("/ai/job/<job_id>/cancel")
    def ai_job_cancel(job_id: str):
        ok = jobstore.cancel(job_id)
        bus.publish("ui.ai.job.cancel", {"id": job_id, "ok": ok, "ts": time.time()})
        return redirect(url_for("ai_jobs"))

    @app.get("/ai/progress")
    def ai_progress():
        job_id = (request.args.get("job_id") or "").strip()
        if not job_id:
            abort(400)

        raw = bus.tail(limit=200, topic_prefix="ai.")
        events = []
        for event in raw:
            payload = event.payload or {}
            if payload.get("job_id") == job_id:
                events.append(
                    {
                        "ts": event.ts,
                        "topic": event.topic,
                        "payload": payload,
                    }
                )
        events = events[-60:]

        return Response(
            response=json.dumps({"job_id": job_id, "events": events}, ensure_ascii=False, indent=2),
            status=200,
            mimetype="application/json",
        )

    if os.environ.get("SMO_AI_WORKER", "0") == "1":
        from smolotchi.ai.worker import AIWorker

        cfg = store.get()
        policy = _build_policy(cfg)
        action_runner = ActionRunner(
            bus=bus, artifacts=artifacts, policy=policy, registry=registry
        )
        worker = AIWorker(
            bus=bus,
            registry=registry,
            artifacts=artifacts,
            jobstore=jobstore,
            runner=action_runner,
        )
        worker.start()
        bus.publish("ai.worker.enabled", {"ts": time.time()})

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8080, debug=False)
