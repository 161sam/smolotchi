from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _now_utc() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_exec_summary(
    bundles: List[Dict[str, Any]],
    top_findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    total_changed = 0
    transitions: Dict[str, int] = {}

    for bundle in bundles:
        diff_badges = bundle.get("diff_badges") or {}
        total_changed += int(diff_badges.get("changed_hosts") or 0)
        for key, value in (diff_badges.get("transitions") or {}).items():
            transitions[key] = int(transitions.get(key, 0)) + int(value or 0)

    return {
        "generated_at": _now_utc(),
        "bundles_considered": len(bundles),
        "top_findings": top_findings,
        "diff": {
            "changed_hosts_total": total_changed,
            "transitions_total": transitions,
        },
    }


def render_exec_summary_md(summary: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Smolotchi LAN Executive Summary")
    lines.append("")
    lines.append(f"- Generated: {summary.get('generated_at')}")
    lines.append(f"- Bundles considered: {summary.get('bundles_considered')}")
    lines.append("")

    diff = summary.get("diff") or {}
    lines.append("## Change Overview")
    lines.append(
        f"- Changed hosts (total across bundles): {diff.get('changed_hosts_total', 0)}"
    )
    transitions = diff.get("transitions_total") or {}
    if transitions:
        for key, value in transitions.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- (no transitions)")
    lines.append("")

    lines.append("## Top Findings")
    top = summary.get("top_findings") or []
    if not top:
        lines.append("- (none)")
    else:
        for finding in top:
            sev = (finding.get("severity") or "info").upper()
            title = finding.get("title") or finding.get("id")
            count = finding.get("count") or 0
            suppressed_count = finding.get("suppressed_count") or 0
            suffix = f" (suppressed: {suppressed_count})" if suppressed_count else ""
            lines.append(f"- **[{sev}]** {title} — hosts: {count}{suffix}")
    lines.append("")
    return "\n".join(lines)


def render_exec_summary_html(summary: Dict[str, Any]) -> str:
    md = render_exec_summary_md(summary)
    escaped = (
        md.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f"""<!doctype html>
<html>
<head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Smolotchi Executive Summary</title>
<style>
body{{background:#0b1016;color:#e7eef7;font-family:system-ui;margin:0;padding:18px}}
.wrap{{max-width:980px;margin:0 auto}}
.card{{background:#111a24;border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:14px;margin:12px 0}}
a{{color:#5fd1ff;text-decoration:none}} a:hover{{text-decoration:underline}}
pre{{white-space:pre-wrap;word-break:break-word;margin:0}}
.row{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
.pill{{padding:4px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.04);font-weight:900;font-size:12px}}
</style>
</head>
<body>
<div class=\"wrap\">
  <div class=\"card\">
    <div class=\"row\" style=\"justify-content:space-between\">
      <div style=\"font-weight:900\">LAN Executive Summary</div>
      <div class=\"row\">
        <a class=\"pill\" href=\"/lan/results\">LAN Results</a>
        <a class=\"pill\" href=\"/lan/summary.md\">MD</a>
        <a class=\"pill\" href=\"/lan/summary.json\">JSON</a>
      </div>
    </div>
  </div>

  <div class=\"card\"><pre>{escaped}</pre></div>
</div>
</body>
</html>"""
