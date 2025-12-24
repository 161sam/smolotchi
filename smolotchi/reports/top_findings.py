from __future__ import annotations

from typing import Any, Dict, List


def aggregate_top_findings(
    bundles: List[Dict[str, Any]],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """
    Returns:
      { id, title, severity, hosts, count, suppressed_count, suppressed_hosts }
    """
    agg: Dict[str, Dict[str, Any]] = {}

    for bundle in bundles:
        summary = bundle.get("host_summary") or {}
        findings = summary.get("findings") or []

        for finding in findings:
            fid = finding.get("id") or finding.get("title")
            if not fid:
                continue

            entry = agg.setdefault(
                str(fid),
                {
                    "id": str(fid),
                    "title": finding.get("title", str(fid)),
                    "severity": finding.get("severity", "info"),
                    "hosts": set(),
                    "suppressed_hosts": set(),
                    "suppressed_count": 0,
                },
            )

            hosts = finding.get("hosts", []) or []
            suppressed = bool(finding.get("suppressed") or finding.get("suppressed_by_policy"))
            if suppressed:
                for host in hosts:
                    entry["suppressed_hosts"].add(host)
            else:
                for host in hosts:
                    entry["hosts"].add(host)

    out = []
    for entry in agg.values():
        hosts = sorted(entry["hosts"])
        suppressed_hosts = sorted(entry["suppressed_hosts"])
        out.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "severity": entry["severity"],
                "hosts": hosts,
                "count": len(hosts),
                "suppressed_hosts": suppressed_hosts,
                "suppressed_count": len(suppressed_hosts),
            }
        )

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    out.sort(
        key=lambda x: (
            order.get(x["severity"], 9),
            -(x["count"] + x["suppressed_count"]),
        )
    )

    return out[:limit]
