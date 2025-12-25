from __future__ import annotations

PRESETS = {
    "stealth": {
        "lock_during_lan": True,
        "disconnect_after_lan": True,
        "lan_throttle_rps": 0.5,
        "lan_batch_size": 2,
        "lan_pack": "bjorn_core",
    },
    "safe": {
        "lock_during_lan": True,
        "disconnect_after_lan": True,
        "lan_throttle_rps": 1.0,
        "lan_batch_size": 4,
        "lan_pack": "bjorn_core",
    },
    "fast": {
        "lock_during_lan": True,
        "disconnect_after_lan": False,
        "lan_throttle_rps": 4.0,
        "lan_batch_size": 16,
        "lan_pack": "bjorn_core",
    },
}
