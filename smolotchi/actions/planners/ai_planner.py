from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal
import time

from smolotchi.actions.registry import ActionRegistry
from smolotchi.core.bus import SQLiteBus

PlanMode = Literal["plan_only", "autonomous_safe"]


@dataclass
class PlanStep:
    action_id: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionPlan:
    id: str
    created_ts: float
    mode: PlanMode
    scope: str
    steps: List[PlanStep]
    note: str = ""


class AIPlanner:
    """
    v0.1: rule-based.
    Produces a plan that includes network_scan + vuln_assess actions.
    """

    def __init__(self, bus: SQLiteBus, registry: ActionRegistry) -> None:
        self.bus = bus
        self.registry = registry

    def generate(
        self,
        scope: str,
        mode: PlanMode,
        note: str = "",
        include_vuln_assess: bool = True,
    ) -> ActionPlan:
        pid = f"plan-{int(time.time())}"
        steps: List[PlanStep] = []

        if self.registry.get("net.host_discovery"):
            steps.append(PlanStep("net.host_discovery", {"scope": scope}))

        plan = ActionPlan(
            id=pid,
            created_ts=time.time(),
            mode=mode,
            scope=scope,
            steps=steps,
            note=note,
        )
        self.bus.publish(
            "ai.plan.created",
            {
                "id": plan.id,
                "mode": plan.mode,
                "scope": plan.scope,
                "steps": [s.action_id for s in steps],
                "expand_hosts": True,
                "include_vuln_assess": include_vuln_assess,
            },
        )
        return plan
