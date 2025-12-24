from __future__ import annotations

from typing import Any, Dict, List


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

        out.append({**script, "tag": tag})
    return out
