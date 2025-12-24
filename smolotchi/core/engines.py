from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol


@dataclass
class EngineHealth:
    name: str
    ok: bool
    detail: str = ""
    ts: float = 0.0


class Engine(Protocol):
    name: str

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def tick(self) -> None: ...
    def health(self) -> EngineHealth: ...


class EngineRegistry:
    def __init__(self) -> None:
        self._engines: Dict[str, Engine] = {}

    def register(self, engine: Engine) -> None:
        self._engines[engine.name] = engine

    def all(self) -> List[Engine]:
        return list(self._engines.values())

    def get(self, name: str) -> Optional[Engine]:
        return self._engines.get(name)

    def health_all(self) -> List[EngineHealth]:
        out: List[EngineHealth] = []
        now = time.time()
        for engine in self.all():
            health = engine.health()
            if not health.ts:
                health.ts = now
            out.append(health)
        return out
