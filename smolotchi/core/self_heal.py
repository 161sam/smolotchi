import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SelfHealer:
    window_sec: float = 60.0
    max_failures: int = 3
    failures: Dict[str, List[float]] = field(default_factory=dict)

    def report(self, engine: str) -> None:
        self.failures.setdefault(engine, []).append(time.time())

    def clear(self, engine: str) -> None:
        if engine in self.failures:
            self.failures.pop(engine, None)

    def should_restart(self, engine: str) -> bool:
        now = time.time()
        times = [t for t in self.failures.get(engine, []) if now - t < self.window_sec]
        self.failures[engine] = times
        return len(times) >= self.max_failures
