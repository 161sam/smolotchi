from __future__ import annotations

from typing import Any, Dict, List


def aggregate_top_findings(
    bundles: List[Dict[str, Any]],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    """
    Returns a list of:
      { id, title, severity, hosts, count }
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
                fid,
                {
                    "id": fid,
                    "title": finding.get("title", fid),
                    "severity": finding.get("severity", "info"),
                    "hosts": set(),
                },
            )

            for host in finding.get("hosts", []):
                entry["hosts"].add(host)

    out = []
    for entry in agg.values():
        out.append(
            {
                "id": entry["id"],
                "title": entry["title"],
                "severity": entry["severity"],
                "hosts": sorted(entry["hosts"]),
                "count": len(entry["hosts"]),
            }
        )

    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    out.sort(key=lambda x: (order.get(x["severity"], 9), -x["count"]))

    return out[:limit]
