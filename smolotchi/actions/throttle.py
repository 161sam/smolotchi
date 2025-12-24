from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional


@dataclass
class ThrottleDecision:
    multiplier: float
    reason: str


def read_loadavg_1m() -> float:
    try:
        return os.getloadavg()[0]
    except Exception:
        return 0.0


def read_cpu_temp_c() -> Optional[float]:
    candidates = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/hwmon/hwmon0/temp1_input",
    ]
    for path in candidates:
        try:
            value = Path(path).read_text(encoding="utf-8").strip()
            temp = float(value)
            if temp > 1000:
                temp = temp / 1000.0
            return temp
        except Exception:
            continue
    return None


def decide_multiplier(cfg, load1: float, temp_c: Optional[float]) -> ThrottleDecision:
    multiplier = 1.0
    reasons = []

    if load1 >= cfg.loadavg_hard:
        multiplier = max(multiplier, cfg.cooldown_multiplier_hard)
        reasons.append(f"loadavg_hard({load1:.2f})")
    elif load1 >= cfg.loadavg_soft:
        multiplier = max(multiplier, cfg.cooldown_multiplier_soft)
        reasons.append(f"loadavg_soft({load1:.2f})")

    if cfg.use_cpu_temp and temp_c is not None:
        if temp_c >= cfg.temp_hard_c:
            multiplier = max(multiplier, cfg.temp_multiplier_hard)
            reasons.append(f"temp_hard({temp_c:.1f}C)")
        elif temp_c >= cfg.temp_soft_c:
            multiplier = max(multiplier, cfg.temp_multiplier_soft)
            reasons.append(f"temp_soft({temp_c:.1f}C)")

    return ThrottleDecision(
        multiplier=multiplier, reason=",".join(reasons) if reasons else "ok"
    )
