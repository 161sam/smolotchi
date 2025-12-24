from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _ts_human(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def build_report_json(model: Dict[str, Any]) -> Dict[str, Any]:
    return model


def build_report_markdown(model: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(f"# {model.get('title','Smolotchi Report')}")
    lines.append("")
    lines.append(f"- Plan: `{model.get('plan_id')}`")
    lines.append(f"- Scope: `{model.get('scope')}`")
    lines.append(f"- Time: {_ts_human(float(model.get('ts', 0) or 0))}")
    lines.append("")

    hosts = model.get("hosts", []) or []
    for host in hosts:
        ip = host.get("ip")
        sev = (host.get("sev_highest") or "info").upper()
        counts = host.get("sev_counts") or {}
        lines.append(f"## {ip} — {sev}")
        lines.append(
            "- Counts: "
            f"C={counts.get('critical',0)} H={counts.get('high',0)} "
            f"M={counts.get('medium',0)} L={counts.get('low',0)} "
            f"I={counts.get('info',0)}"
        )
        lines.append(
            f"- Open ports: {', '.join(map(str, host.get('open_ports', []) or [])) or '—'}"
        )
        lines.append("")
        badges = host.get("badges", []) or []
        if badges:
            lines.append("**Top badges**")
            for badge in badges:
                lines.append(f"- {badge}")
            lines.append("")

        findings = ((host.get("findings") or {}).get("scripts") or [])
        if findings:
            lines.append("**Findings (safe snippets)**")
            for finding in findings[:12]:
                cvss = finding.get("cvss")
                cvss_str = f" (CVSS {cvss})" if isinstance(cvss, (int, float)) else ""
                lines.append(
                    f"- `{finding.get('severity','info')}`{cvss_str} "
                    f"`{finding.get('id')}` `{finding.get('scope')}`: "
                    f"{finding.get('output','').replace('\\n',' / ')[:180]}"
                )
            lines.append("")
        else:
            lines.append("_No script findings extracted._")
            lines.append("")

    return "\n".join(lines)
