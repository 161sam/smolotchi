from __future__ import annotations

import hashlib
import ipaddress
import json

RPS_MIN, RPS_MAX = 0.1, 50.0
BATCH_MIN, BATCH_MAX = 1, 256


def normalize_profile(profile: dict) -> tuple[dict, list[str]]:
    """
    Returns (normalized_profile, warnings)
    """
    p = dict(profile or {})
    warnings = []

    # scope
    scope = p.get("scope")
    if scope:
        try:
            net = ipaddress.ip_network(str(scope), strict=False)
            p["scope"] = str(net)
        except Exception:
            warnings.append(f"invalid scope '{scope}', removed")
            p.pop("scope", None)

    # throttle rps
    rps = p.get("lan_throttle_rps")
    if rps is not None:
        try:
            rps = float(rps)
            if rps < RPS_MIN:
                warnings.append(f"lan_throttle_rps too low ({rps}), clamped to {RPS_MIN}")
                rps = RPS_MIN
            if rps > RPS_MAX:
                warnings.append(f"lan_throttle_rps too high ({rps}), clamped to {RPS_MAX}")
                rps = RPS_MAX
            p["lan_throttle_rps"] = round(rps, 3)
        except Exception:
            warnings.append(f"invalid lan_throttle_rps '{rps}', removed")
            p.pop("lan_throttle_rps", None)

    # batch size
    bs = p.get("lan_batch_size")
    if bs is not None:
        try:
            bs = int(bs)
            if bs < BATCH_MIN:
                warnings.append(f"lan_batch_size too small ({bs}), clamped to {BATCH_MIN}")
                bs = BATCH_MIN
            if bs > BATCH_MAX:
                warnings.append(f"lan_batch_size too large ({bs}), clamped to {BATCH_MAX}")
                bs = BATCH_MAX
            p["lan_batch_size"] = bs
        except Exception:
            warnings.append(f"invalid lan_batch_size '{bs}', removed")
            p.pop("lan_batch_size", None)

    return p, warnings


def profile_hash(profile: dict) -> str:
    blob = json.dumps(profile, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(blob).hexdigest()[:12]
