from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict


def _ts(ts: float) -> str:
    return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def host_diff_markdown(diff: Dict[str, Any], host: str) -> str:
    per = diff.get("per_host") or {}
    h = per.get(host) or {}

    lines = []
    lines.append(f"# Host Diff • {host}")
    lines.append("")
    lines.append(
        f"- Prev host_summary: `{diff.get('prev_host_summary_id') or diff.get('prev_id')}` "
        f"@ {_ts(diff.get('ts_prev', 0) or 0)}"
    )
    lines.append(
        f"- Cur  host_summary: `{diff.get('cur_host_summary_id') or diff.get('cur_id')}` "
        f"@ {_ts(diff.get('ts_cur', 0) or 0)}"
    )
    lines.append("")

    if host in (diff.get("hosts_added") or []):
        lines.append("**Status:** added")
    elif host in (diff.get("hosts_removed") or []):
        lines.append("**Status:** removed")
    else:
        lines.append("**Status:** changed")
    lines.append("")

    if h.get("ports"):
        lines.append("## Ports")
        lines.append(f"- prev: `{h['ports']['prev']}`")
        lines.append(f"- cur:  `{h['ports']['cur']}`")
        lines.append("")

    if h.get("fingerprints"):
        lines.append("## Fingerprints (by key)")
        for key, value in (h.get("fingerprints") or {}).items():
            lines.append(f"- {key}: {value['prev']} → {value['cur']}")
        lines.append("")

    if h.get("severity_counts"):
        sc = h["severity_counts"]
        lines.append("## Severity")
        lines.append(f"- highest: {sc.get('prev_highest')} → {sc.get('cur_highest')}")
        lines.append(f"- counts prev: {sc.get('prev')}")
        lines.append(f"- counts cur:  {sc.get('cur')}")
        lines.append("")

    if not any([h.get("ports"), h.get("fingerprints"), h.get("severity_counts")]):
        lines.append("_No detailed changes recorded for this host._")
        lines.append("")

    links = h.get("links") or {}
    if links:
        lines.append("## Artifacts")
        for side in ("prev", "cur"):
            amap = links.get(side) or {}
            if not amap:
                continue
            lines.append(f"### {side}")
            if "net.port_scan" in amap:
                lines.append(f"- net.port_scan: {', '.join(amap['net.port_scan'])}")
            for key in sorted([k for k in amap.keys() if k.startswith("vuln.")]):
                lines.append(f"- {key}: {', '.join(amap[key])}")
            lines.append("")

    return "\n".join(lines)


def _artifact_links_html(amap: dict) -> str:
    parts = []
    for art_id in amap.get("net.port_scan") or []:
        parts.append(
            "<div><a href='/artifact/{0}'>port_scan {0}</a> · "
            "<a href='/artifact/{0}/download'>dl</a></div>".format(art_id)
        )
    for action_id in sorted([k for k in amap.keys() if k.startswith("vuln.")]):
        for art_id in amap.get(action_id) or []:
            parts.append(
                "<div><a href='/artifact/{0}'>{1} {0}</a> · "
                "<a href='/artifact/{0}/download'>dl</a></div>".format(
                    art_id, action_id
                )
            )
    return "".join(parts) or "<div class='muted'>—</div>"


def host_diff_html(diff: Dict[str, Any], host: str) -> str:
    md = (
        host_diff_markdown(diff, host)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    per = diff.get("per_host") or {}
    h = per.get(host) or {}
    links = h.get("links") or {}
    link_blocks = []
    for side in ("prev", "cur"):
        amap = links.get(side) or {}
        if not amap:
            continue
        link_blocks.append(
            "<div class='artifact-side'><div class='artifact-title'>"
            f"{side}</div>{_artifact_links_html(amap)}</div>"
        )
    artifacts_html = ""
    if link_blocks:
        artifacts_html = (
            "<div class='card'><h3>Artifacts</h3>"
            + "".join(link_blocks)
            + "</div>"
        )
    return (
        "<!doctype html><html><head><meta charset='utf-8'/>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'/>"
        "<title>Host Diff</title>"
        "<style>body{background:#0b1016;color:#e7eef7;font-family:system-ui;margin:0;"
        "padding:18px}pre{white-space:pre-wrap;background:#111a24;"
        "border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:14px}"
        ".card{margin-top:16px;background:#111a24;border:1px solid "
        "rgba(255,255,255,.10);border-radius:16px;padding:14px}"
        ".artifact-title{font-weight:700;margin:6px 0}"
        ".artifact-side{margin-bottom:10px}"
        "a{color:#8ac7ff;text-decoration:none}.muted{opacity:.7}</style>"
        "</head><body><pre>"
        f"{md}"
        "</pre>"
        f"{artifacts_html}"
        "</body></html>"
    )
