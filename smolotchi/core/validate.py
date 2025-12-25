from __future__ import annotations

import ipaddress


def validate_profiles(profiles: dict) -> list[str]:
    errs: list[str] = []
    if not isinstance(profiles, dict):
        return ["profiles is not a dict"]

    for ssid, p in profiles.items():
        if not isinstance(p, dict):
            errs.append(f"{ssid}: profile not a dict")
            continue

        scope = p.get("scope")
        if scope:
            try:
                ipaddress.ip_network(str(scope), strict=False)
            except Exception:
                errs.append(f"{ssid}: invalid scope CIDR: {scope}")

        rps = p.get("lan_throttle_rps")
        if rps is not None:
            try:
                rpsf = float(rps)
                if rpsf <= 0 or rpsf > 50:
                    errs.append(f"{ssid}: lan_throttle_rps out of range (0..50]: {rps}")
            except Exception:
                errs.append(f"{ssid}: lan_throttle_rps not a number: {rps}")

        bs = p.get("lan_batch_size")
        if bs is not None:
            try:
                bsi = int(bs)
                if bsi < 1 or bsi > 256:
                    errs.append(f"{ssid}: lan_batch_size out of range [1..256]: {bs}")
            except Exception:
                errs.append(f"{ssid}: lan_batch_size not an int: {bs}")

    return errs
