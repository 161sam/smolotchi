from __future__ import annotations

from typing import Any, Dict, List
import time

from smolotchi.actions.registry import ActionRegistry
from smolotchi.actions.runner import ActionRunner
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus


class PlanRunner:
    def __init__(
        self,
        bus: SQLiteBus,
        registry: ActionRegistry,
        runner: ActionRunner,
        artifacts: ArtifactStore,
    ) -> None:
        self.bus = bus
        self.registry = registry
        self.runner = runner
        self.artifacts = artifacts

    def run(self, plan: Dict[str, Any], mode: str) -> Dict[str, Any]:
        t0 = time.time()
        out_steps: List[Dict[str, Any]] = []
        self.bus.publish("plan.started", {"id": plan.get("id"), "mode": mode})

        for step in plan.get("steps", []):
            aid = step.get("action_id")
            payload = step.get("payload", {}) or {}
            spec = self.registry.get(aid)
            if not spec:
                out_steps.append({"action_id": aid, "ok": False, "reason": "unknown_action"})
                continue

            res = self.runner.run(spec, payload, mode=mode)
            out_steps.append(
                {
                    "action_id": aid,
                    "ok": res.ok,
                    "artifact_id": res.artifact_id,
                    "summary": res.summary,
                    "meta": res.meta or {},
                }
            )

        result = {
            "plan_id": plan.get("id"),
            "scope": plan.get("scope"),
            "mode": mode,
            "steps": out_steps,
            "duration_s": time.time() - t0,
            "ts": time.time(),
        }
        meta = self.artifacts.put_json(
            kind="plan_run",
            title=f"Plan run • {plan.get('id')}",
            payload=result,
        )
        self.bus.publish(
            "plan.finished",
            {"id": plan.get("id"), "artifact_id": meta.id, "ok": all(s["ok"] for s in out_steps)},
        )
        result["artifact_id"] = meta.id
        return result
