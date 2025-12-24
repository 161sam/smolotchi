import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Optional

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.engines import EngineHealth


@dataclass
class LanJob:
    id: str
    kind: str
    scope: str
    created_ts: float = field(default_factory=lambda: time.time())
    note: str = ""


@dataclass
class LanConfig:
    enabled: bool = True
    safe_mode: bool = True
    max_jobs_per_tick: int = 1


class LanEngine:
    name = "lan"

    def __init__(self, bus: SQLiteBus, cfg: LanConfig, artifacts: ArtifactStore):
        self.bus = bus
        self.cfg = cfg
        self.artifacts = artifacts
        self._running = False
        self._q: Deque[LanJob] = deque()
        self._active: Optional[LanJob] = None

    def start(self) -> None:
        self._running = True
        self.bus.publish("lan.engine.started", {"safe_mode": self.cfg.safe_mode})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("lan.engine.stopped", {})

    def enqueue(self, job: LanJob) -> None:
        self._q.append(job)
        self.bus.publish(
            "lan.job.enqueued",
            {"id": job.id, "kind": job.kind, "scope": job.scope, "note": job.note},
        )

    def tick(self) -> None:
        if not self._running or not self.cfg.enabled:
            return

        if self._active is None and self._q:
            self._active = self._q.popleft()
            self.bus.publish(
                "lan.job.started",
                {
                    "id": self._active.id,
                    "kind": self._active.kind,
                    "scope": self._active.scope,
                },
            )

        if self._active is not None:
            result = {
                "job": {
                    "id": self._active.id,
                    "kind": self._active.kind,
                    "scope": self._active.scope,
                    "note": self._active.note,
                },
                "summary": "stub result (v0.0.5)",
                "ts": time.time(),
            }

            meta = self.artifacts.put_json(
                kind="lan_result",
                title=f"LAN {self._active.kind} • {self._active.scope}",
                payload=result,
            )

            self.bus.publish("lan.job.progress", {"id": self._active.id, "pct": 100})
            self.bus.publish(
                "lan.job.finished",
                {
                    "id": self._active.id,
                    "result": {
                        "summary": "stub",
                        "artifact_id": meta.id,
                        "artifact_path": meta.path,
                    },
                },
            )
            self._active = None

    def health(self) -> EngineHealth:
        if not self.cfg.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        detail = (
            f"running q={len(self._q)} active={'yes' if self._active else 'no'}"
            if self._running
            else "stopped"
        )
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
