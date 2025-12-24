import time
from dataclasses import dataclass
from typing import Literal

from .bus import SQLiteBus
from .policy import Policy

State = Literal["WIFI_OBSERVE", "HANDOFF_PREPARE", "LAN_OPS", "IDLE"]


@dataclass
class CoreStatus:
    state: State
    since: float
    note: str = ""
    last_event: str = ""


class SmolotchiCore:
    """
    v0.0.1: Nur Orchestrierung/State + Events.
    Engines (wifi/lan) kommen in späteren Milestones als separate Module/Services.
    """

    def __init__(self, bus: SQLiteBus, policy: Policy):
        self.bus = bus
        self.policy = policy
        self.status = CoreStatus(state="WIFI_OBSERVE", since=time.time())

    def set_state(self, state: State, note: str = "") -> None:
        self.status = CoreStatus(state=state, since=time.time(), note=note)
        self.bus.publish(
            "core.state.changed", {"state": state, "note": note, "ts": self.status.since}
        )

    def tick(self) -> None:
        """
        Später: hier reagierst du auf wifi-events, lan-job-queue etc.
        Für v0.0.1 simulieren wir:
        - wenn ein "handoff.request" kommt und policy ok -> HANDOFF_PREPARE -> LAN_OPS
        - wenn "lan.done" -> zurück WIFI_OBSERVE
        """
        events = self.bus.tail(limit=10)
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
