from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str], timeout: int = 20) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, f"{proc.stdout}\n{proc.stderr}"


def connect_wpa_psk(
    iface: str, ssid: str, psk: str, workdir: str = "/run/smolotchi"
) -> tuple[bool, str]:
    """
    Lab-safe: connect only using provided credentials.
    Uses wpa_supplicant + dhclient.
    """
    Path(workdir).mkdir(parents=True, exist_ok=True)
    conf = Path(workdir) / f"wpa_{iface}.conf"
    conf.write_text(
        "ctrl_interface=DIR={}\n"
        "update_config=0\n\n"
        "network={{\n"
        '  ssid="{}"\n'
        '  psk="{}"\n'
        "}}\n".format(workdir, ssid, psk),
        encoding="utf-8",
    )

    _run(["pkill", "-f", f"wpa_supplicant.*{iface}"], timeout=5)

    rc, out = _run(["wpa_supplicant", "-B", "-i", iface, "-c", str(conf)], timeout=20)
    if rc != 0:
        return False, out

    _run(["dhclient", "-r", iface], timeout=10)
    rc, out2 = _run(["dhclient", iface], timeout=25)
    if rc != 0:
        return False, f"{out}\n{out2}"

    return True, f"{out}\n{out2}"


def disconnect_wpa(iface: str) -> tuple[bool, str]:
    _run(["dhclient", "-r", iface], timeout=10)
    rc, out = _run(["pkill", "-f", f"wpa_supplicant.*{iface}"], timeout=5)
    return True, out
