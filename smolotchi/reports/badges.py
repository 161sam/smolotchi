from __future__ import annotations

from typing import Any, Dict

SEV_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def _rank(sev: str) -> int:
    return SEV_RANK.get((sev or "info").lower(), 0)


def summarize_host_findings(
    findings: Dict[str, Any], top_n: int = 3
) -> Dict[str, Any]:
    scripts = findings.get("scripts") or []

    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for finding in scripts:
        sev = (finding.get("severity") or "info").lower()
        if sev not in counts:
            sev = "info"
        counts[sev] += 1

    def key(finding: Dict[str, Any]) -> Any:
        sev = (finding.get("severity") or "info").lower()
        cvss = finding.get("cvss")
        cv = float(cvss) if isinstance(cvss, (int, float)) else -1.0
        return (-_rank(sev), -cv, finding.get("tag", ""), finding.get("scope", ""), finding.get("id", ""))

    top = sorted(scripts, key=key)[:top_n]
    badges = []
    for finding in top:
        sev = (finding.get("severity") or "info").upper()
        sid = finding.get("id") or "script"
        scope = finding.get("scope") or "host"
        cvss = finding.get("cvss")
        cv = f" CVSS {cvss}" if isinstance(cvss, (int, float)) else ""
        badges.append(f"{sev}{cv} • {sid} • {scope}")

    highest = "info"
    for sev in ("critical", "high", "medium", "low", "info"):
        if counts.get(sev, 0) > 0:
            highest = sev
            break

    return {"counts": counts, "highest": highest, "badges": badges}
