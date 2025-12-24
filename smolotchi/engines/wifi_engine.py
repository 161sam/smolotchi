import time
from dataclasses import dataclass

from smolotchi.core.bus import SQLiteBus
from smolotchi.core.engines import EngineHealth


@dataclass
class WifiConfig:
    enabled: bool = True
    safe_mode: bool = True


class WifiEngine:
    name = "wifi"

    def __init__(self, bus: SQLiteBus, cfg: WifiConfig):
        self.bus = bus
        self.cfg = cfg
        self._running = False
        self._last_tick = 0.0

    def start(self) -> None:
        self._running = True
        self.bus.publish("wifi.engine.started", {"safe_mode": self.cfg.safe_mode})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("wifi.engine.stopped", {})

    def tick(self) -> None:
        if not self._running or not self.cfg.enabled:
            return
        now = time.time()
        if now - self._last_tick > 5.0:
            self.bus.publish("wifi.telemetry.heartbeat", {"ts": now})
            self._last_tick = now

    def health(self) -> EngineHealth:
        if not self.cfg.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        detail = "running" if self._running else "stopped"
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
