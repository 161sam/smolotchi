from __future__ import annotations

import re
import subprocess


def _run(cmd: list[str], timeout: int = 6) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + "\n" + (p.stderr or "")


def default_gateway(iface: str) -> str | None:
    rc, out = _run(["ip", "route", "show", "default", "dev", iface], timeout=4)
    if rc != 0:
        return None
    match = re.search(r"\bvia\s+(\d+\.\d+\.\d+\.\d+)\b", out)
    return match.group(1) if match else None


def has_default_route(iface: str) -> bool:
    rc, out = _run(["ip", "route", "show", "default", "dev", iface], timeout=4)
    return rc == 0 and "default" in out


def ping(host: str, iface: str | None = None) -> bool:
    cmd = ["ping", "-c", "1", "-W", "1", host]
    if iface:
        cmd = ["ping", "-I", iface, "-c", "1", "-W", "1", host]
    rc, _ = _run(cmd, timeout=4)
    return rc == 0


def health_check(
    iface: str, ping_gateway: bool = True, ping_target: str | None = None
) -> dict:
    gw = default_gateway(iface)
    route_ok = has_default_route(iface)
    gw_ok = ping(gw, iface=iface) if (ping_gateway and gw) else None
    target_ok = ping(ping_target, iface=iface) if ping_target else None
    ok = bool(route_ok) and (True if gw_ok is None else gw_ok) and (
        True if target_ok is None else target_ok
    )
    return {
        "iface": iface,
        "ok": ok,
        "route_ok": route_ok,
        "gateway": gw,
        "gateway_ok": gw_ok,
        "target": ping_target,
        "target_ok": target_ok,
    }
