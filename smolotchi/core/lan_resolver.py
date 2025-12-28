from __future__ import annotations

from typing import Any, Dict


def resolve_result_by_job_id(job_id: str, artifacts) -> Dict[str, Any]:
    """
    Preferred resolver:
    1) Try lan_job_result artifacts (stable mapping)
    Fallback resolver:
    2) Try lan_bundle by job_id (fast)
    3) Else: scan artifacts index for lan_result/lan_report and correlate via content.job.id
    """
    if not job_id:
        return {}

    for artifact in artifacts.list(limit=50, kind="lan_job_result"):
        payload = artifacts.get_json(artifact.id)
        if not isinstance(payload, dict):
            continue
        if str(payload.get("job_id")) != job_id:
            continue
        bundle_id = payload.get("bundle_id")
        report_id = payload.get("report_id")
        bundle = artifacts.get_json(bundle_id) if bundle_id else None
        json_id = None
        if bundle and isinstance(bundle, dict):
            json_id = (bundle.get("result_json") or {}).get("artifact_id")
        return {
            "bundle_id": bundle_id,
            "bundle": bundle,
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
            "ok": payload.get("ok"),
        }

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
            "ok": True,
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
        "ok": None,
    }
