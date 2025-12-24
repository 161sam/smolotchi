from __future__ import annotations

from typing import Any, Dict, List

from smolotchi.reports.severity import infer_severity


def classify_scripts(scripts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for script in scripts or []:
        sid = (script.get("id") or "").lower()
        tag = "info"
        if sid.startswith(("vuln", "vulners")):
            tag = "vuln"
        elif sid.startswith(("http-", "ssl-", "tls-")):
            tag = "web"
        elif sid.startswith(("ssh-",)):
            tag = "ssh"
        elif sid.startswith(("smb",)):
            tag = "smb"
        elif sid.startswith(("rdp-",)):
            tag = "rdp"

        sev, cvss, reason = infer_severity(script.get("output") or "", script_id=sid)

        out.append(
            {
                **script,
                "tag": tag,
                "severity": sev,
                "cvss": cvss,
                "sev_reason": reason,
            }
        )
    return out
