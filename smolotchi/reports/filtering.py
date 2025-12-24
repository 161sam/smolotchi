from __future__ import annotations

from typing import Any, Dict, List


def apply_policy_suppression(
    findings: List[Dict[str, Any]],
    cfg: Any,
) -> List[Dict[str, Any]]:
    """
    Marks findings as suppressed_by_policy instead of removing them.
    Policy sources:
      cfg.lan.noisy_scripts: list[str]
      cfg.lan.allowlist_scripts: list[str]
      cfg.lan.suppress: dict (optional future)
    """
    lan_cfg = cfg.get("lan") if isinstance(cfg, dict) else getattr(cfg, "lan", None)
    if lan_cfg is None:
        lan_cfg = {}
    noisy = set(
        (x or "").strip().lower()
        for x in (
            lan_cfg.get("noisy_scripts", [])
            if isinstance(lan_cfg, dict)
            else getattr(lan_cfg, "noisy_scripts", [])
        )
        or []
        if (x or "").strip()
    )
    allow = set(
        (x or "").strip().lower()
        for x in (
            lan_cfg.get("allowlist_scripts", [])
            if isinstance(lan_cfg, dict)
            else getattr(lan_cfg, "allowlist_scripts", [])
        )
        or []
        if (x or "").strip()
    )

    out: List[Dict[str, Any]] = []

    for f in findings:
        script_id = (f.get("script_id") or f.get("script") or f.get("id") or "").strip()
        script_key = script_id.lower()

        suppressed = False
        reason = ""

        if script_key and script_key in allow:
            suppressed = False
        elif script_key and script_key in noisy:
            suppressed = True
            reason = f"script suppressed by policy: {script_id}"

        if suppressed:
            f = dict(f)
            f["suppressed_by_policy"] = True
            f["suppressed_reason"] = reason
            f.setdefault("original_severity", f.get("severity", "info"))

        out.append(f)

    return out


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
