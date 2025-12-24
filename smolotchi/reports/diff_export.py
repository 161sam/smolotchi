from __future__ import annotations

from typing import Any, Dict
import json
from datetime import datetime, timezone


def _ts(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def diff_markdown(diff: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Smolotchi • Host Diff")
    lines.append("")
    lines.append(
        f"- Prev: `{diff.get('prev_host_summary_id')}` @ {_ts(diff.get('ts_prev', 0) or 0)}"
    )
    lines.append(
        f"- Cur:  `{diff.get('cur_host_summary_id')}` @ {_ts(diff.get('ts_cur', 0) or 0)}"
    )
    lines.append("")
    if diff.get("hosts_added"):
        lines.append("## Hosts added")
        for host in diff["hosts_added"]:
            lines.append(f"- {host}")
        lines.append("")
    if diff.get("hosts_removed"):
        lines.append("## Hosts removed")
        for host in diff["hosts_removed"]:
            lines.append(f"- {host}")
        lines.append("")
    ch_hosts = diff.get("changed_hosts") or []
    if ch_hosts:
        lines.append("## Changed hosts")
        for host in ch_hosts:
            lines.append(f"- {host}")
        lines.append("")
    else:
        lines.append("## Changed hosts")
        lines.append("_No changes detected._")
        lines.append("")

    per = diff.get("per_host") or {}
    for host in ch_hosts:
        hdiff = per.get(host) or {}
        lines.append(f"### {host}")
        if hdiff.get("ports"):
            lines.append(
                f"- ports: `{hdiff['ports']['prev']}` → `{hdiff['ports']['cur']}`"
            )
        if hdiff.get("fingerprints"):
            parts = [
                f"{key}: {value['prev']}→{value['cur']}"
                for key, value in (hdiff.get("fingerprints") or {}).items()
            ]
            lines.append("- fp: " + ", ".join(parts))
        if hdiff.get("severity_counts"):
            sc = hdiff["severity_counts"]
            lines.append(
                f"- severity: {sc['prev_highest']}→{sc['cur_highest']} "
                f"(C {sc['prev']['critical']}→{sc['cur']['critical']}, "
                f"H {sc['prev']['high']}→{sc['cur']['high']}, "
                f"M {sc['prev']['medium']}→{sc['cur']['medium']}, "
                f"L {sc['prev']['low']}→{sc['cur']['low']}, "
                f"I {sc['prev']['info']}→{sc['cur']['info']})"
            )
        lines.append("")
    lines.append("")
    return "\n".join(lines)


def diff_html(diff: Dict[str, Any]) -> str:
    md = (
        diff_markdown(diff)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<title>Smolotchi Diff</title>"
        "<style>body{background:#0b1016;color:#e7eef7;font-family:system-ui;margin:0;"
        "padding:18px}pre{white-space:pre-wrap;background:#111a24;"
        "border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:14px}"
        "</style></head><body><pre>"
        f"{md}"
        "</pre></body></html>"
    )


def diff_json(diff: Dict[str, Any]) -> bytes:
    return json.dumps(diff, ensure_ascii=False, indent=2).encode("utf-8")
