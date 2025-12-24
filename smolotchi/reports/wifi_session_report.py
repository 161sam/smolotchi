from __future__ import annotations

from html import escape
from typing import Any, Dict


def wifi_session_html(session: Dict[str, Any]) -> str:
    def row(key: str, value: str) -> str:
        return (
            "<tr>"
            f"<td style='padding:8px 10px;opacity:.7'>{escape(key)}</td>"
            f"<td style='padding:8px 10px;font-weight:800'>{escape(value)}</td>"
            "</tr>"
        )

    title = f"WiFi Session {session.get('id')}"
    ssid = str(session.get("ssid") or "")
    iface = str(session.get("iface") or "")
    scope = str(session.get("scope") or "")
    reason = str(session.get("reason") or "")
    dur = str(session.get("duration_sec") or "")
    ts1 = str(session.get("ts_start") or "")
    ts2 = str(session.get("ts_end") or "")

    return f"""<!doctype html>
<html><head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{escape(title)}</title>
<style>
  body{{background:#0b1220;color:#e7eef7;font-family:ui-sans-serif,system-ui; padding:20px;}}
  .card{{background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.10); border-radius:16px; padding:16px; max-width:900px;}}
  h1{{margin:0 0 10px 0;font-size:18px}}
  table{{width:100%; border-collapse:collapse; margin-top:10px}}
  tr{{border-top:1px solid rgba(255,255,255,.08)}}
</style>
</head>
<body>
  <div class="card">
    <h1>{escape(title)}</h1>
    <div style="opacity:.75">Quick view</div>
    <table>
      {row("SSID", ssid)}
      {row("Interface", iface)}
      {row("Scope", scope)}
      {row("Reason", reason)}
      {row("Duration (sec)", dur)}
      {row("Start (epoch)", ts1)}
      {row("End (epoch)", ts2)}
    </table>
  </div>
</body></html>
"""
