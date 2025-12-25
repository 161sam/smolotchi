from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Literal, Optional

from smolotchi.actions.registry import ActionRegistry
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus

PlanMode = Literal["plan_only", "autonomous_safe"]


@dataclass(frozen=True)
class PlanCandidate:
    action_id: str
    params: Dict[str, Any]
    score: float
    why: List[str]
    evidence: List[Dict[str, Any]]
    risk: str
    cost: Dict[str, float]


@dataclass
class PlanStep:
    action_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    why: List[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class ActionPlan:
    id: str
    created_ts: float
    mode: PlanMode
    scope: str
    steps: List[PlanStep]
    note: str = ""
    seed: Optional[int] = None
    explain: Dict[str, Any] = field(default_factory=dict)


class AIPlanner:
    """
    Smolotchi AI Planner v1 (Research)

    - Deterministic
    - Policy-gated
    - Explainable
    - Registry-driven
    - No exploitation by default

    Future:
    - RL hook points
    - Exploit selection gates
    """

    def __init__(
        self,
        bus: SQLiteBus,
        registry: ActionRegistry,
        *,
        seed: Optional[int] = None,
        artifacts: Optional[ArtifactStore] = None,
    ) -> None:
        self.bus = bus
        self.registry = registry
        self.seed = seed
        self.artifacts = artifacts

        self.weights = {
            "novelty": 2.0,
            "severity": 1.5,
            "staleness": 1.0,
            "coverage": 1.0,
            "uncertainty": 0.8,
            "noise": 1.2,
            "cost": 1.0,
            "risk": 3.0,
        }

        self.allowed_risks = {"safe", "noisy"}

    def generate(
        self,
        scope: str,
        mode: PlanMode,
        note: str = "",
        include_vuln_assess: bool = True,
    ) -> ActionPlan:
        ts = time.time()
        pid = f"plan-{int(ts)}"

        candidates = self._generate_candidates(
            scope=scope,
            include_vuln_assess=include_vuln_assess,
        )

        candidates = [c for c in candidates if c.risk in self.allowed_risks]

        candidates.sort(
            key=lambda c: (-c.score, c.risk, c.cost.get("time_s", 0), c.action_id)
        )

        steps: List[PlanStep] = [
            PlanStep(
                action_id=c.action_id,
                payload=c.params,
                why=c.why,
                score=round(c.score, 3),
            )
            for c in candidates
        ]

        explain = {
            "weights": self.weights,
            "allowed_risks": sorted(self.allowed_risks),
            "candidate_count": len(candidates),
            "ranking": [
                {
                    "action_id": c.action_id,
                    "score": round(c.score, 3),
                    "risk": c.risk,
                    "cost": c.cost,
                    "why": c.why,
                }
                for c in candidates
            ],
        }

        plan = ActionPlan(
            id=pid,
            created_ts=ts,
            mode=mode,
            scope=scope,
            steps=steps,
            note=note,
            seed=self.seed,
            explain=explain,
        )

        artifact_id = None
        if self.artifacts:
            plan_doc = {
                "id": plan.id,
                "created_ts": plan.created_ts,
                "mode": plan.mode,
                "scope": plan.scope,
                "note": plan.note,
                "seed": plan.seed,
                "steps": [
                    {
                        "action_id": s.action_id,
                        "payload": s.payload,
                        "why": s.why,
                        "score": s.score,
                    }
                    for s in plan.steps
                ],
                "explain": plan.explain,
            }
            meta = self.artifacts.put_json(
                kind="ai_plan",
                title=f"AI Plan {plan.id}",
                payload=plan_doc,
                tags=["ai", "plan", plan.mode],
                meta={"scope": plan.scope},
            )
            artifact_id = meta.id

        self.bus.publish(
            "ai.plan.created",
            {
                "id": plan.id,
                "mode": plan.mode,
                "scope": plan.scope,
                "steps": [s.action_id for s in plan.steps],
                "explain": plan.explain,
                "seed": self.seed,
                "artifact_id": artifact_id,
            },
        )

        return plan

    def _generate_candidates(
        self,
        *,
        scope: str,
        include_vuln_assess: bool,
    ) -> List[PlanCandidate]:
        out: List[PlanCandidate] = []

        if self.registry.get("net.host_discovery"):
            out.append(
                self._candidate(
                    action_id="net.host_discovery",
                    params={"scope": scope},
                    novelty=0.6,
                    severity=0.0,
                    staleness=0.8,
                    coverage=1.0,
                    uncertainty=0.5,
                    noise=0.2,
                    cost={"time_s": 10, "ops": 1},
                    risk="safe",
                    why=["initial inventory for scope"],
                )
            )

        if self.registry.get("net.port_scan"):
            out.append(
                self._candidate(
                    action_id="net.port_scan",
                    params={"scope": scope},
                    novelty=0.5,
                    severity=0.1,
                    staleness=0.9,
                    coverage=1.0,
                    uncertainty=0.6,
                    noise=0.3,
                    cost={"time_s": 25, "ops": 2},
                    risk="safe",
                    why=["port state required for service discovery"],
                )
            )

        if include_vuln_assess and self.registry.get("vuln.assess.safe"):
            out.append(
                self._candidate(
                    action_id="vuln.assess.safe",
                    params={"scope": scope},
                    novelty=0.4,
                    severity=0.6,
                    staleness=0.7,
                    coverage=0.8,
                    uncertainty=0.4,
                    noise=0.4,
                    cost={"time_s": 40, "ops": 3},
                    risk="noisy",
                    why=["baseline vulnerability coverage"],
                )
            )

        return out

    def _candidate(
        self,
        *,
        action_id: str,
        params: Dict[str, Any],
        novelty: float,
        severity: float,
        staleness: float,
        coverage: float,
        uncertainty: float,
        noise: float,
        cost: Dict[str, float],
        risk: str,
        why: List[str],
    ) -> PlanCandidate:
        score = (
            self.weights["novelty"] * novelty
            + self.weights["severity"] * severity
            + self.weights["staleness"] * staleness
            + self.weights["coverage"] * coverage
            + self.weights["uncertainty"] * uncertainty
            - self.weights["noise"] * noise
            - self.weights["cost"] * self._norm_cost(cost)
            - self.weights["risk"] * self._risk_penalty(risk)
        )

        return PlanCandidate(
            action_id=action_id,
            params=params,
            score=score,
            why=why,
            evidence=[],
            risk=risk,
            cost=cost,
        )

    def _norm_cost(self, cost: Dict[str, float]) -> float:
        time_s = cost.get("time_s", 0.0)
        return min(time_s / 60.0, 1.0)

    def _risk_penalty(self, risk: str) -> float:
        if risk == "safe":
            return 0.0
        if risk == "noisy":
            return 0.5
        if risk == "intrusive":
            return 1.5
        if risk == "dangerous":
            return 3.0
        return 1.0
