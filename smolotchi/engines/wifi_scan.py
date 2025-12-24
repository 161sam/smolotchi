from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import List


@dataclass
class WifiAP:
    ssid: str
    bssid: str
    freq_mhz: int | None
    channel: int | None
    signal_dbm: int | None
    security: str | None


def _run(cmd: list[str], timeout: int = 15) -> str:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return f"{proc.stdout}\n{proc.stderr}"


def scan_iw(iface: str) -> List[WifiAP]:
    """
    Uses: iw dev <iface> scan
    Parses minimal fields: SSID, BSSID, freq, signal.
    """
    out = _run(["iw", "dev", iface, "scan"], timeout=20)
    aps: List[WifiAP] = []

    cur = {"bssid": None, "ssid": "", "freq": None, "signal": None, "sec": None}
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("BSS "):
            if cur["bssid"]:
                aps.append(
                    WifiAP(
                        ssid=cur["ssid"] or "",
                        bssid=cur["bssid"],
                        freq_mhz=cur["freq"],
                        channel=None,
                        signal_dbm=cur["signal"],
                        security=cur["sec"],
                    )
                )
            cur = {
                "bssid": line.split()[1],
                "ssid": "",
                "freq": None,
                "signal": None,
                "sec": None,
            }
        elif line.startswith("freq:"):
            try:
                cur["freq"] = int(line.split(":")[1].strip())
            except ValueError:
                continue
        elif line.startswith("signal:"):
            try:
                cur["signal"] = int(float(line.split()[1]))
            except ValueError:
                continue
        elif line.startswith("SSID:"):
            cur["ssid"] = line.split("SSID:", 1)[1].strip()
        elif "WPA:" in line or "RSN:" in line:
            cur["sec"] = "wpa2+"

    if cur["bssid"]:
        aps.append(
            WifiAP(
                ssid=cur["ssid"] or "",
                bssid=cur["bssid"],
                freq_mhz=cur["freq"],
                channel=None,
                signal_dbm=cur["signal"],
                security=cur["sec"],
            )
        )

    return aps
