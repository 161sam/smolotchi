from __future__ import annotations

from typing import Any, Dict, List

SEV_RANK = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


def apply_normalization(
    scripts: List[Dict[str, Any]],
    normalize_cfg: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not normalize_cfg or not normalize_cfg.get("enabled", True):
        return scripts

    force_severity = normalize_cfg.get("force_severity") or {}
    force_tag = normalize_cfg.get("force_tag") or {}

    force_severity_l = {str(k).lower(): str(v).lower() for k, v in force_severity.items()}
    force_tag_l = {str(k).lower(): str(v).lower() for k, v in force_tag.items()}

    out: List[Dict[str, Any]] = []
    for script in scripts or []:
        sid = str(script.get("id") or "").lower()
        sev = str(script.get("severity") or "info").lower()

        if sid in force_severity_l:
            sev = force_severity_l[sid]
            script = {**script, "severity": sev, "sev_reason": "normalized:force_severity"}

        if sid in force_tag_l:
            sev = force_tag_l[sid]
            script = {**script, "severity": sev, "sev_reason": "normalized:force_tag"}

        out.append(script)
    return out
