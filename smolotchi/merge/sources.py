from __future__ import annotations

from typing import Any, Dict, List


def _safe_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def find_wifi_context_for_job(
    artifacts, job_id: str, limit: int = 200
) -> Dict[str, Any]:
    """
    Scan newest wifi_lan_timeline entries and return the newest entry matching job_id.
    """
    for meta in artifacts.list(limit=limit, kind="wifi_lan_timeline"):
        payload = artifacts.get_json(meta.id)
        p = _safe_dict(payload)
        if str(p.get("job_id") or "") == job_id:
            return {"meta": meta, "payload": p}
    return {}


def list_policy_events_for_job(bus, job_id: str, limit: int = 500) -> List[Dict[str, Any]]:
    """
    Heuristic: scan recent events and pick those with job_id / request_id correlation.
    Later we’ll switch to explicit policy artifacts.
    """
    out: List[Dict[str, Any]] = []
    for e in bus.tail(limit=limit):
        payload = _safe_dict(getattr(e, "payload", None))
        if str(payload.get("job_id") or "") == job_id:
            out.append({"ts": getattr(e, "ts", None), "topic": e.topic, "payload": payload})
            continue
        job = payload.get("job") if isinstance(payload.get("job"), dict) else None
        if job and str(job.get("id") or "") == job_id:
            out.append({"ts": getattr(e, "ts", None), "topic": e.topic, "payload": payload})
    return out


def list_host_summaries_for_job(
    artifacts, job_id: str, limit: int = 2000
) -> List[Dict[str, Any]]:
    """
    Preferred: host_summary artifacts carry job_id in payload.meta/job_id (we’ll standardize this).
    Fallback: scan newest host_summary and accept those within same time window (handled in timeline merge).
    """
    items: List[Dict[str, Any]] = []
    for meta in artifacts.list(limit=limit, kind="host_summary"):
        payload = artifacts.get_json(meta.id)
        p = _safe_dict(payload)
        if str(p.get("job_id") or "") == job_id:
            items.append({"meta": meta, "payload": p})
            continue
        meta2 = p.get("meta") if isinstance(p.get("meta"), dict) else {}
        if str(meta2.get("job_id") or "") == job_id:
            items.append({"meta": meta, "payload": p})
    return items


def get_lan_result_for_job(resolve_result_by_job_id, job_id: str) -> Dict[str, Any]:
    return resolve_result_by_job_id(job_id) or {}
