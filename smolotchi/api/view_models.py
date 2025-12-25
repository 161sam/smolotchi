from __future__ import annotations

from smolotchi.core.normalize import normalize_profile, profile_hash


def effective_lan_overrides(app_cfg, job_meta: dict | None) -> dict:
    job_meta = job_meta or {}
    lan_over = (
        (job_meta.get("lan_overrides") or {}) if isinstance(job_meta, dict) else {}
    )
    wifi_profile = (
        (job_meta.get("wifi_profile") or {}) if isinstance(job_meta, dict) else {}
    )
    wifi_profile_hash = (
        job_meta.get("wifi_profile_hash") if isinstance(job_meta, dict) else None
    )

    lan_cfg = getattr(app_cfg, "lan", None)
    default_pack = (
        getattr(lan_cfg, "default_pack", "bjorn_core") if lan_cfg else "bjorn_core"
    )
    default_rps = float(getattr(lan_cfg, "throttle_rps", 1.0) or 1.0) if lan_cfg else 1.0
    default_batch = int(getattr(lan_cfg, "batch_size", 4) or 4) if lan_cfg else 4

    if wifi_profile and not wifi_profile_hash:
        norm, _ = normalize_profile(wifi_profile)
        wifi_profile_hash = profile_hash(norm)

    current_hash = None
    drift = False
    wifi_ssid = job_meta.get("wifi_ssid") if isinstance(job_meta, dict) else None
    if wifi_ssid:
        wcfg = getattr(app_cfg, "wifi", None)
        profiles = getattr(wcfg, "profiles", None) if wcfg else None
        if isinstance(profiles, dict):
            cur = profiles.get(wifi_ssid) or {}
            if isinstance(cur, dict):
                cur_norm, _ = normalize_profile(cur)
                current_hash = profile_hash(cur_norm)
                drift = bool(wifi_profile_hash and wifi_profile_hash != current_hash)

    eff = {
        "wifi_ssid": wifi_ssid,
        "wifi_iface": job_meta.get("wifi_iface"),
        "pack": lan_over.get("pack") or default_pack,
        "throttle_rps": lan_over.get("throttle_rps")
        if lan_over.get("throttle_rps") is not None
        else default_rps,
        "batch_size": lan_over.get("batch_size")
        if lan_over.get("batch_size") is not None
        else default_batch,
        "wifi_profile": wifi_profile,
        "lan_overrides": lan_over,
        "profile_hash": wifi_profile_hash,
        "profile_current_hash": current_hash,
        "profile_drift": drift,
    }
    return eff
