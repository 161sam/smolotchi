from __future__ import annotations

from typing import Any, Dict, List

from .sources import (
    find_wifi_context_for_job,
    get_lan_result_for_job,
    list_host_summaries_for_job,
    list_policy_events_for_job,
)


def _safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _ts(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def build_dossier(
    *,
    job_id: str,
    scope: str | None,
    bus,
    artifacts,
    resolve_result_by_job_id,
) -> Dict[str, Any]:
    if not job_id:
        return {}

    lan = get_lan_result_for_job(resolve_result_by_job_id, job_id)
    wifi_ctx = find_wifi_context_for_job(artifacts, job_id)
    policy_events = list_policy_events_for_job(bus, job_id)
    host_rows = list_host_summaries_for_job(artifacts, job_id)

    hosts: List[Dict[str, Any]] = []
    for row in host_rows:
        p = _safe_dict(row.get("payload"))
        hosts.append(p)

    timeline: List[Dict[str, Any]] = []

    if wifi_ctx:
        p = _safe_dict(wifi_ctx.get("payload"))
        timeline.append(
            {
                "ts": _ts(p.get("ts")),
                "type": "wifi.lan.timeline",
                "ssid": p.get("ssid"),
                "iface": p.get("iface"),
                "wifi_profile_hash": p.get("wifi_profile_hash"),
                "scope": p.get("scope"),
                "reason": p.get("reason"),
                "artifact_id": wifi_ctx["meta"].id,
            }
        )

    for pe in policy_events:
        payload = _safe_dict(pe.get("payload"))
        timeline.append(
            {
                "ts": _ts(pe.get("ts") or payload.get("ts")),
                "type": "policy.event",
                "topic": pe.get("topic"),
                "payload": payload,
            }
        )

    if lan:
        timeline.append(
            {
                "ts": _ts(lan.get("ts") or 0),
                "type": "lan.result",
                "bundle_id": lan.get("bundle_id"),
                "report_id": lan.get("report_id"),
                "ok": lan.get("ok"),
            }
        )

    for h in hosts:
        host_block = h.get("host") if isinstance(h.get("host"), dict) else {}
        timeline.append(
            {
                "ts": _ts(h.get("last_seen") or h.get("ts") or 0),
                "type": "lan.host",
                "ip": host_block.get("ip") or h.get("ip"),
                "ports": h.get("ports") or [],
                "services": h.get("services") or [],
                "sources": h.get("sources") or [],
            }
        )

    timeline_sorted = sorted(timeline, key=lambda x: _ts(x.get("ts")))

    decisions: List[Dict[str, Any]] = []
    for item in timeline_sorted:
        if item.get("type") != "policy.event":
            continue
        topic = item.get("topic") or ""
        payload = _safe_dict(item.get("payload"))
        if "policy" in topic or "approval" in topic or "blocked" in topic:
            decisions.append(
                {
                    "ts": item.get("ts"),
                    "topic": topic,
                    "action": payload.get("action")
                    or payload.get("op")
                    or payload.get("kind"),
                    "decision": payload.get("decision")
                    or payload.get("status")
                    or payload.get("result"),
                    "note": payload.get("note"),
                    "by": payload.get("by"),
                }
            )

    eff_scope = scope
    if not eff_scope and wifi_ctx:
        eff_scope = (_safe_dict(wifi_ctx.get("payload"))).get("scope")

    dossier = {
        "ts": _ts(timeline_sorted[-1]["ts"]) if timeline_sorted else 0,
        "job_id": job_id,
        "scope": eff_scope or "",
        "wifi": {
            "ssid": (_safe_dict(wifi_ctx.get("payload"))).get("ssid") if wifi_ctx else None,
            "iface": (_safe_dict(wifi_ctx.get("payload"))).get("iface") if wifi_ctx else None,
            "wifi_profile_hash": (
                _safe_dict(wifi_ctx.get("payload"))
            ).get("wifi_profile_hash")
            if wifi_ctx
            else None,
            "reason": (_safe_dict(wifi_ctx.get("payload"))).get("reason")
            if wifi_ctx
            else None,
            "timeline_artifact_id": wifi_ctx["meta"].id if wifi_ctx else None,
        },
        "policy": {"decisions": decisions},
        "lan": {
            "bundle_id": lan.get("bundle_id") if isinstance(lan, dict) else None,
            "report_id": lan.get("report_id") if isinstance(lan, dict) else None,
            "ok": lan.get("ok") if isinstance(lan, dict) else None,
        },
        "hosts": {"count": len(hosts), "items": hosts},
        "timeline": timeline_sorted,
    }
    return dossier
