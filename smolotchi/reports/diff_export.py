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
    lines.append("## Changes")
    for change in diff.get("changes", []):
        if change["type"] == "ports":
            lines.append(
                f"- **{change['host']}** ports: `{change['prev']}` → `{change['cur']}`"
            )
        elif change["type"] == "fingerprints":
            parts = [
                f"{key}: {value['prev']}→{value['cur']}"
                for key, value in (change.get("changes") or {}).items()
            ]
            lines.append(f"- **{change['host']}** fp: " + ", ".join(parts))
    if not diff.get("changes"):
        lines.append("_No changes detected._")
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
