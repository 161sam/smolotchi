from __future__ import annotations

from typing import Any, Dict, List, Optional
import time
from datetime import datetime, timezone
import json

from jinja2 import Environment, FileSystemLoader, select_autoescape

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.reports.badges import summarize_host_findings
from smolotchi.reports.findings_aggregate import build_host_findings


def _ts_human(ts: float) -> str:
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S UTC"
        )
    except Exception:
        return str(ts)


def _extract_host_from_action_run(art: Dict[str, Any]) -> str:
    payload = art.get("payload") if isinstance(art.get("payload"), dict) else {}
    return str((payload or {}).get("target") or "")


def _action_summary(art: Dict[str, Any]) -> str:
    rc = art.get("returncode")
    if rc is None:
        rc = art.get("meta", {}).get("rc") if isinstance(art.get("meta"), dict) else None
    if rc is not None:
        return f"rc={rc}"
    return "ok"


def build_aggregate_model(
    artifacts: ArtifactStore,
    host_summary_artifact_id: str,
    *,
    title: str = "Smolotchi • Aggregate Report",
    scope_override: Optional[str] = None,
    report_cfg: Optional[dict] = None,
    bundle_id: Optional[str] = None,
) -> Dict[str, Any]:
    hs = artifacts.get_json(host_summary_artifact_id) or {}
    plan_id = hs.get("plan_id")
    scope = scope_override or hs.get("scope")
    ts = float(hs.get("ts", time.time()) or time.time())

    hosts_map = hs.get("hosts") or {}
    artifacts_list = hs.get("artifacts") or []

    per_host_actions: Dict[str, List[Dict[str, Any]]] = {h: [] for h in hosts_map.keys()}

    for ref in artifacts_list:
        aid = ref.get("action_id")
        art_id = ref.get("artifact_id")
        if not art_id:
            continue
        art = artifacts.get_json(art_id) or {}
        host = _extract_host_from_action_run(art)
        if not host:
            continue
        per_host_actions.setdefault(host, []).append(
            {
                "action_id": aid,
                "artifact_id": art_id,
                "summary": _action_summary(art),
            }
        )

    findings = build_host_findings(artifacts, hs, cfg=report_cfg or {})

    hosts: List[Dict[str, Any]] = []
    for host_ip, hdata in hosts_map.items():
        ports_by_key = hdata.get("ports_by_key") or {
            "http": [],
            "ssh": [],
            "smb": [],
        }
        fp_by_key = hdata.get("fp_by_key") or {"http": "", "ssh": "", "smb": ""}

        open_ports = sorted(
            set(
                (ports_by_key.get("http") or [])
                + (ports_by_key.get("ssh") or [])
                + (ports_by_key.get("smb") or [])
            )
        )

        host_find = findings.get(host_ip) or {}
        hf = {
            "ports": host_find.get("ports", []),
            "scripts": host_find.get("scripts", []),
        }
        badge = summarize_host_findings(hf, top_n=3)

        hosts.append(
            {
                "ip": host_ip,
                "ports_by_key": ports_by_key,
                "fp_by_key": fp_by_key,
                "open_ports": open_ports,
                "actions": per_host_actions.get(host_ip, []),
                "findings": hf,
                "badges": badge.get("badges", []),
                "sev_counts": badge.get("counts", {}),
                "sev_highest": badge.get("highest", "info"),
            }
        )

    hosts.sort(
        key=lambda x: (
            -{"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}.get(
                x.get("sev_highest", "info"), 0
            ),
            x["ip"],
        )
    )

    job = hs.get("job") if isinstance(hs.get("job"), dict) else {}
    job_meta = {}
    if isinstance(job, dict):
        job_meta = job.get("meta") if isinstance(job.get("meta"), dict) else {}
    if not job_meta and isinstance(hs.get("job_meta"), dict):
        job_meta = hs.get("job_meta") or {}
    wifi_profile = (
        job_meta.get("wifi_profile") if isinstance(job_meta, dict) else {}
    ) or {}
    lan_overrides = (
        job_meta.get("lan_overrides") if isinstance(job_meta, dict) else {}
    ) or {}

    applied = {
        "wifi_ssid": job_meta.get("wifi_ssid") if isinstance(job_meta, dict) else None,
        "wifi_iface": job_meta.get("wifi_iface") if isinstance(job_meta, dict) else None,
        "wifi_profile": wifi_profile,
        "lan_overrides": lan_overrides,
        "wifi_profile_json": json.dumps(
            wifi_profile, ensure_ascii=False, indent=2, sort_keys=True
        )
        if wifi_profile
        else "",
        "lan_overrides_json": json.dumps(
            lan_overrides, ensure_ascii=False, indent=2, sort_keys=True
        )
        if lan_overrides
        else "",
        "effective": {
            "scope": (job.get("scope") if isinstance(job, dict) else None) or scope,
            "pack": lan_overrides.get("pack")
            if isinstance(lan_overrides, dict)
            else None,
            "throttle_rps": lan_overrides.get("throttle_rps")
            if isinstance(lan_overrides, dict)
            else None,
            "batch_size": lan_overrides.get("batch_size")
            if isinstance(lan_overrides, dict)
            else None,
        },
    }

    return {
        "title": title,
        "plan_id": plan_id,
        "scope": scope,
        "ts": ts,
        "hosts": hosts,
        "host_summary_artifact_id": host_summary_artifact_id,
        "bundle_id": bundle_id,
        "applied": applied,
    }


def build_aggregate_report(
    artifacts: ArtifactStore,
    host_summary_artifact_id: str,
    *,
    title: str = "Smolotchi • Aggregate Report",
    bundle_id: Optional[str] = None,
    report_cfg: Optional[dict] = None,
) -> str:
    model = build_aggregate_model(
        artifacts,
        host_summary_artifact_id,
        title=title,
        report_cfg=report_cfg,
        bundle_id=bundle_id,
    )
    env = Environment(
        loader=FileSystemLoader("smolotchi/reports/templates"),
        autoescape=select_autoescape(["html"]),
    )
    tpl = env.get_template("report_aggregate.html")
    html = tpl.render(
        title=model.get("title"),
        plan_id=model.get("plan_id"),
        scope=model.get("scope"),
        ts_human=_ts_human(float(model.get("ts", 0) or 0)),
        hosts=model.get("hosts", []),
        host_summary_artifact_id=model.get("host_summary_artifact_id"),
        bundle_id=model.get("bundle_id"),
        applied=model.get("applied"),
    )
    return html
