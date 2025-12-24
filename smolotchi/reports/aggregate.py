from __future__ import annotations

from typing import Any, Dict, List, Optional
import time
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader, select_autoescape

from smolotchi.core.artifacts import ArtifactStore


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


def build_aggregate_report(
    artifacts: ArtifactStore,
    host_summary_artifact_id: str,
    *,
    title: str = "Smolotchi • Aggregate Report",
    bundle_id: Optional[str] = None,
) -> str:
    hs = artifacts.get_json(host_summary_artifact_id) or {}
    plan_id = hs.get("plan_id")
    scope = hs.get("scope")
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

        hosts.append(
            {
                "ip": host_ip,
                "ports_by_key": ports_by_key,
                "fp_by_key": fp_by_key,
                "open_ports": open_ports,
                "actions": per_host_actions.get(host_ip, []),
            }
        )

    hosts.sort(key=lambda x: x["ip"])

    env = Environment(
        loader=FileSystemLoader("smolotchi/reports/templates"),
        autoescape=select_autoescape(["html"]),
    )
    tpl = env.get_template("report_aggregate.html")
    html = tpl.render(
        title=title,
        plan_id=plan_id,
        scope=scope,
        ts_human=_ts_human(ts),
        hosts=hosts,
        host_summary_artifact_id=host_summary_artifact_id,
        bundle_id=bundle_id,
    )
    return html
