from __future__ import annotations

from typing import Any, Dict, List


def filter_findings_scripts(
    scripts: List[Dict[str, Any]],
    *,
    allowlist: List[str] | None = None,
    denylist: List[str] | None = None,
    deny_contains: List[str] | None = None,
) -> List[Dict[str, Any]]:
    allow = set([(x or "").strip().lower() for x in (allowlist or []) if (x or "").strip()])
    deny = set([(x or "").strip().lower() for x in (denylist or []) if (x or "").strip()])
    contains = [(x or "").strip().lower() for x in (deny_contains or []) if (x or "").strip()]

    out = []
    for script in scripts or []:
        sid = (script.get("id") or "").strip().lower()
        out_text = (script.get("output") or "").lower()

        if sid in deny:
            continue
        if contains and any(c in out_text for c in contains):
            continue
        if allow and sid not in allow:
            continue

        out.append(script)
    return out
