from __future__ import annotations

import time
from typing import Any, Dict


def build_lan_dossier(
    *,
    job_id: str,
    scope: str = "",
    reason: str = "manual",
    artifacts,
    jobstore,
    resolve_result_by_job_id,
    policy_lookup=None,
    hostsummary_lookup=None,
) -> str:
    """
    Create a lan_dossier artifact that merges:
      - WiFi→LAN timeline entry (best-effort)
      - LAN result bundle/report resolution
      - policy decisions (best-effort)
      - host summaries (best-effort)
    Returns artifact_id of the dossier.
    """
    if not job_id:
        raise ValueError("job_id is required")

    ts = time.time()

    resolved = resolve_result_by_job_id(job_id, artifacts) or {}
    bundle_id = resolved.get("bundle_id")
    report_id = resolved.get("report_id")
    ok = resolved.get("ok")

    job = jobstore.get(job_id) if jobstore else None
    eff_scope = scope
    if not eff_scope and job and getattr(job, "scope", None):
        eff_scope = str(job.scope)

    wifi: Dict[str, Any] = {}
    try:
        for meta in artifacts.list(limit=80, kind="wifi_lan_timeline"):
            payload = artifacts.get_json(meta.id) or {}
            if isinstance(payload, dict) and str(payload.get("job_id") or "") == job_id:
                wifi = {
                    "ssid": payload.get("ssid"),
                    "iface": payload.get("iface"),
                    "wifi_profile_hash": payload.get("wifi_profile_hash"),
                    "scope": payload.get("scope"),
                    "ts": payload.get("ts"),
                    "reason": payload.get("reason"),
                    "artifact_id": meta.id,
                }
                if not eff_scope:
                    eff_scope = str(payload.get("scope") or "")
                break
    except Exception:
        wifi = {}

    policy: Dict[str, Any] = {}
    if policy_lookup:
        try:
            policy = policy_lookup(job_id) or {}
        except Exception:
            policy = {}

    hosts: Dict[str, Any] = {}
    if hostsummary_lookup:
        try:
            hosts = hostsummary_lookup(job_id, eff_scope) or {}
        except Exception:
            hosts = {}

    dossier = {
        "ts": ts,
        "job_id": job_id,
        "scope": eff_scope,
        "reason": reason,
        "wifi": wifi,
        "lan": {
            "ok": ok,
            "bundle_id": bundle_id,
            "report_id": report_id,
        },
        "policy": policy,
        "hosts": hosts,
        "timeline": [],
    }

    artifact_id = artifacts.put_json(
        kind="lan_dossier",
        title=f"lan dossier {job_id}",
        payload=dossier,
        meta={"job_id": job_id, "scope": eff_scope, "ts": ts},
    ).id
    return artifact_id
