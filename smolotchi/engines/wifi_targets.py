from __future__ import annotations

import time
from typing import Any, Dict, List


def update_targets_state(
    state: Dict[str, Any], aps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    now = time.time()
    st = state or {}
    targets = st.get("targets") or {}
    if not isinstance(targets, dict):
        targets = {}

    for ap in aps:
        bssid = (ap.get("bssid") or "").strip()
        ssid = (ap.get("ssid") or "").strip()
        if not bssid:
            continue

        cur = targets.get(bssid) or {}
        seen = int(cur.get("seen_count") or 0) + 1

        sig = ap.get("signal")
        try:
            sig = int(sig) if sig is not None else None
        except Exception:
            sig = None

        strongest = cur.get("strongest_signal_dbm")
        if strongest is None:
            strongest = sig
        else:
            try:
                strongest = max(int(strongest), sig) if sig is not None else int(strongest)
            except Exception:
                strongest = sig

        targets[bssid] = {
            "ssid": ssid,
            "bssid": bssid,
            "last_seen_ts": now,
            "seen_count": seen,
            "last_signal_dbm": sig,
            "strongest_signal_dbm": strongest,
            "security": ap.get("sec"),
            "freq_mhz": ap.get("freq"),
        }

    st["updated_ts"] = now
    st["targets"] = targets
    return st
