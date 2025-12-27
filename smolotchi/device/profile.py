from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DeviceProfile:
    name: str

    display_refresh_min_s: float = 3.0
    display_tick_s: float = 5.0

    artifacts_keep_days: int = 14
    artifacts_keep_max: int = 3000

    low_battery_percent: Optional[int] = 15
    critical_battery_percent: Optional[int] = 8

    btn_next_pin: Optional[int] = 5
    btn_mode_pin: Optional[int] = 6
    btn_ok_pin: Optional[int] = 13

    default_cooldown_s: float = 1.5


def get_device_profile(name: str) -> DeviceProfile:
    key = (name or "").strip().lower()
    if key in ("pi_zero", "pi0", "pi0w", "pi_zero_w"):
        return DeviceProfile(name="pi_zero")
    return DeviceProfile(name="default")
