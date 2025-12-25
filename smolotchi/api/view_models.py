from __future__ import annotations


def effective_lan_overrides(app_cfg, job_meta: dict | None) -> dict:
    job_meta = job_meta or {}
    lan_over = (job_meta.get("lan_overrides") or {}) if isinstance(job_meta, dict) else {}
    wifi_profile = (job_meta.get("wifi_profile") or {}) if isinstance(job_meta, dict) else {}

    lan_cfg = getattr(app_cfg, "lan", None)
    default_pack = getattr(lan_cfg, "default_pack", "bjorn_core") if lan_cfg else "bjorn_core"
    default_rps = float(getattr(lan_cfg, "throttle_rps", 1.0) or 1.0) if lan_cfg else 1.0
    default_batch = int(getattr(lan_cfg, "batch_size", 4) or 4) if lan_cfg else 4

    eff = {
        "wifi_ssid": job_meta.get("wifi_ssid"),
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
    }
    return eff
