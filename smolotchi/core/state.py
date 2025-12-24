import time
from dataclasses import dataclass
from typing import Literal, Optional

from .bus import SQLiteBus
from .engines import EngineRegistry
from .policy import Policy

State = Literal["WIFI_OBSERVE", "HANDOFF_PREPARE", "LAN_OPS", "IDLE"]


@dataclass
class CoreStatus:
    state: State
    since: float
    note: str = ""


class SmolotchiCore:
    def __init__(self, bus: SQLiteBus, policy: Policy, engines: EngineRegistry):
        self.bus = bus
        self.policy = policy
        self.engines = engines
        self.status = CoreStatus(state="WIFI_OBSERVE", since=time.time(), note="boot")

        self._apply_state_engines()

    def set_state(self, state: State, note: str = "") -> None:
        self.status = CoreStatus(state=state, since=time.time(), note=note)
        self.bus.publish(
            "core.state.changed", {"state": state, "note": note, "ts": self.status.since}
        )
        self._apply_state_engines()

    def _apply_state_engines(self) -> None:
        wifi = self.engines.get("wifi")
        lan = self.engines.get("lan")

        def safe_stop(engine) -> None:
            try:
                engine.stop()
            except Exception as ex:
                self.bus.publish(
                    "core.engine.error",
                    {"engine": getattr(engine, "name", "?"), "op": "stop", "err": str(ex)},
                )

        def safe_start(engine) -> None:
            try:
                engine.start()
            except Exception as ex:
                self.bus.publish(
                    "core.engine.error",
                    {"engine": getattr(engine, "name", "?"), "op": "start", "err": str(ex)},
                )

        if self.status.state == "WIFI_OBSERVE":
            if lan:
                safe_stop(lan)
            if wifi:
                safe_start(wifi)
        elif self.status.state == "LAN_OPS":
            if wifi:
                safe_stop(wifi)
            if lan:
                safe_start(lan)
        else:
            if wifi:
                safe_stop(wifi)
            if lan:
                safe_stop(lan)

    def _coerce_lan_job(self, payload: Optional[dict]) -> Optional[object]:
        if not payload:
            return None
        try:
            from smolotchi.engines.lan_engine import LanJob
        except Exception:
            return None
        if isinstance(payload, LanJob):
            return payload
        try:
            return LanJob(**payload)
        except TypeError:
            return None

    def tick(self) -> None:
        events = self.bus.tail(limit=20)
        for e in events:
            if e.topic == "ui.handoff.request":
                if self.policy.allow_handoff(e.payload):
                    self.set_state("HANDOFF_PREPARE", "handoff approved")
                    self.set_state("LAN_OPS", "lan ops running")
                else:
                    self.bus.publish(
                        "core.policy.blocked",
                        {"reason": "handoff not allowed", "payload": e.payload},
                    )

            if e.topic == "lan.done":
                self.set_state("WIFI_OBSERVE", "lan ops finished")

            if e.topic == "ui.lan.enqueue":
                lan = self.engines.get("lan")
                if lan and hasattr(lan, "enqueue"):
                    job = self._coerce_lan_job(e.payload.get("job"))
                    if job:
                        lan.enqueue(job)

        for eng in self.engines.all():
            try:
                eng.tick()
            except Exception as ex:
                self.bus.publish(
                    "core.engine.error",
                    {"engine": getattr(eng, "name", "?"), "op": "tick", "err": str(ex)},
                )

        self.bus.publish(
            "core.health", {"engines": [h.__dict__ for h in self.engines.health_all()]}
        )
