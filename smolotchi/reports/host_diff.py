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

    links = h.get("links") or {}
    if links:
        lines.append("## Artifacts")
        for side in ("prev", "cur"):
            amap = links.get(side) or {}
            lines.append(f"### {side}")
            if not amap:
                lines.append("- —")
                lines.append("")
                continue

            if "net.port_scan" in amap:
                for art_id in amap.get("net.port_scan") or []:
                    lines.append(f"- net.port_scan: {art_id}")

            for key in sorted([k for k in amap.keys() if k.startswith("vuln.")]):
                for art_id in amap.get(key) or []:
                    lines.append(f"- {key}: {art_id}")
            lines.append("")

    if not any([h.get("ports"), h.get("fingerprints"), h.get("severity_counts"), links]):
        lines.append("_No detailed changes recorded for this host._")
        lines.append("")

    return "\n".join(lines)


def host_diff_html(diff: Dict[str, Any], host: str) -> str:
    per = diff.get("per_host") or {}
    h = per.get(host) or {}

    def esc(value: str) -> str:
        return (value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def a_link(art_id: str, label: str) -> str:
        return (
            f"<a href='/artifact/{esc(art_id)}'>{esc(label)}</a>"
            f" <span class='muted'>·</span> "
            f"<a href='/artifact/{esc(art_id)}/download'>dl</a>"
        )

    if host in (diff.get("hosts_added") or []):
        status = "added"
    elif host in (diff.get("hosts_removed") or []):
        status = "removed"
    else:
        status = "changed"

    cards = []

    if h.get("ports"):
        cards.append(
            "<div class='card'>"
            "<div class='h2'>Ports</div>"
            f"<div class='mono'>prev: {esc(str(h['ports']['prev']))}</div>"
            f"<div class='mono'>cur:  {esc(str(h['ports']['cur']))}</div>"
            "</div>"
        )

    if h.get("fingerprints"):
        fp_lines = []
        for key, value in (h.get("fingerprints") or {}).items():
            fp_lines.append(
                f"<div class='mono'>{esc(key)}: {esc(value.get('prev', ''))} → "
                f"{esc(value.get('cur', ''))}</div>"
            )
        cards.append(
            "<div class='card'>"
            "<div class='h2'>Fingerprints</div>"
            + "".join(fp_lines)
            + "</div>"
        )

    if h.get("severity_counts"):
        sc = h["severity_counts"]
        cards.append(
            "<div class='card'>"
            "<div class='h2'>Severity</div>"
            f"<div class='mono'>highest: {esc(str(sc.get('prev_highest', 'info')))} → "
            f"{esc(str(sc.get('cur_highest', 'info')))}</div>"
            f"<div class='mono'>prev: {esc(str(sc.get('prev')))}</div>"
            f"<div class='mono'>cur:  {esc(str(sc.get('cur')))}</div>"
            "</div>"
        )

    links = h.get("links") or {}
    if links:
        def render_side(side: str) -> str:
            amap = links.get(side) or {}
            if not amap:
                return "<div class='muted'>—</div>"

            parts = []

            ps = amap.get("net.port_scan") or []
            if ps:
                parts.append("<div class='h3'>net.port_scan</div>")
                for art_id in ps:
                    parts.append(
                        f"<div>{a_link(art_id, f'net.port_scan {art_id}')} "
                        f"<span class='muted'>·</span> "
                        f"<a href='/artifact/{esc(art_id)}.json' target='_blank'>json</a>"
                        f"</div>"
                    )

            vulns = sorted([k for k in amap.keys() if k.startswith("vuln.")])
            if vulns:
                parts.append("<div class='h3' style='margin-top:10px'>vuln</div>")
                for aid in vulns:
                    for art_id in (amap.get(aid) or []):
                        parts.append(
                            f"<div>{a_link(art_id, f'{aid} {art_id}')} "
                            f"<span class='muted'>·</span> "
                            f"<a href='/artifact/{esc(art_id)}.json' target='_blank'>json</a>"
                            f"</div>"
                        )

            return "".join(parts) if parts else "<div class='muted'>—</div>"

        prev_html = render_side("prev")
        cur_html = render_side("cur")

        cards.append(
            "<div class='card'>"
            "<div class='h2'>Artifacts (Prev / Cur)</div>"
            "<div class='grid2'>"
            "<div class='col'>"
            "<div class='h3'>prev</div>"
            f"{prev_html}"
            "</div>"
            "<div class='col'>"
            "<div class='h3'>cur</div>"
            f"{cur_html}"
            "</div>"
            "</div>"
            "</div>"
        )

    if not cards:
        cards.append("<div class='card'><div class='muted'>No details for this host.</div></div>")

    prev_id = str(diff.get("prev_host_summary_id") or diff.get("prev_id") or "")
    cur_id = str(diff.get("cur_host_summary_id") or diff.get("cur_id") or "")

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Host Diff • {esc(host)}</title>
<style>
  body{{background:#0b1016;color:#e7eef7;font-family:system-ui;margin:0;padding:18px}}
  a{{color:#5fd1ff;text-decoration:none}} a:hover{{text-decoration:underline}}
  .wrap{{max-width:980px;margin:0 auto}}
  .card{{background:#111a24;border:1px solid rgba(255,255,255,.10);border-radius:16px;padding:14px;margin:12px 0}}
  .h1{{font-size:18px;font-weight:900}}
  .h2{{font-size:14px;font-weight:900;margin-bottom:8px}}
  .h3{{font-size:12px;font-weight:900;margin-top:10px}}
  .muted{{color:rgba(231,238,247,.70);font-size:12px}}
  .mono{{font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,"Liberation Mono","Courier New",monospace;font-size:12px}}
  .row{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}
  .pill{{padding:4px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.10);background:rgba(255,255,255,.04);font-weight:800;font-size:12px}}
  .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
  .col{{border:1px solid rgba(255,255,255,.08);border-radius:14px;padding:12px;background:rgba(255,255,255,.02)}}
  @media (max-width: 820px){{.grid2{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <div class="row" style="justify-content:space-between">
      <div>
        <div class="h1">Host Diff • {esc(host)} <span class="muted">({esc(status)})</span></div>
        <div class="muted">Prev: <span class="mono">{esc(prev_id)}</span> · Cur: <span class="mono">{esc(cur_id)}</span></div>
      </div>
      <div class="row">
        <a class="pill" href="/lan">← Back to LAN</a>
      </div>
    </div>
  </div>

  {''.join(cards)}

</div>
</body>
</html>"""
