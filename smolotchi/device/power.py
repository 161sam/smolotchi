from __future__ import annotations

import glob
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class PowerStatus:
    percent: Optional[int]
    source: str
    ts: float


def _read_first_capacity_sysfs() -> Optional[int]:
    for cap in glob.glob("/sys/class/power_supply/*/capacity"):
        try:
            value = int(Path(cap).read_text().strip())
        except ValueError:
            continue
        if 0 <= value <= 100:
            return value
    return None


class PowerMonitor:
    def read(self) -> PowerStatus:
        percent = _read_first_capacity_sysfs()
        source = "sysfs" if percent is not None else "none"
        return PowerStatus(percent=percent, source=source, ts=time.time())

    @staticmethod
    def to_dict(status: PowerStatus) -> Dict[str, Any]:
        return {"percent": status.percent, "source": status.source, "ts": status.ts}
