from __future__ import annotations

import re
import subprocess


def _run(cmd: list[str], timeout: int = 10) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return (p.stdout or "") + "\n" + (p.stderr or "")


def detect_ipv4_cidr(iface: str) -> str | None:
    """
    Returns e.g. '10.0.10.23/24' or None.
    Uses: ip -4 addr show dev <iface>
    """
    out = _run(["ip", "-4", "addr", "show", "dev", iface], timeout=10)
    m = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+/\d+)\b", out)
    return m.group(1) if m else None


def cidr_to_network_scope(cidr: str) -> str | None:
    """
    '10.0.10.23/24' -> '10.0.10.0/24'
    No external libs; pure integer math.
    """
    try:
        ip, prefix_s = cidr.split("/")
        prefix = int(prefix_s)
        parts = [int(x) for x in ip.split(".")]
        if len(parts) != 4 or not (0 <= prefix <= 32):
            return None
        ip_int = (parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]
        mask = (0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF if prefix > 0 else 0
        net = ip_int & mask
        net_ip = (
            f"{(net >> 24) & 255}.{(net >> 16) & 255}."
            f"{(net >> 8) & 255}.{net & 255}"
        )
        return f"{net_ip}/{prefix}"
    except Exception:
        return None


def detect_scope_for_iface(iface: str) -> str | None:
    cidr = detect_ipv4_cidr(iface)
    if not cidr:
        return None
    return cidr_to_network_scope(cidr)
