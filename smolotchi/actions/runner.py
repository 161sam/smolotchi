from __future__ import annotations

from typing import Any, Dict, Optional

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.policy import Policy
from .registry import ActionRegistry, UnknownAction
from .execution import ActionResult


class ActionRunner:
    def __init__(
        self,
        *,
        bus: SQLiteBus,
        artifacts: ArtifactStore,
        policy: Policy,
        registry: ActionRegistry,
    ) -> None:
        self.bus = bus
        self.artifacts = artifacts
        self.policy = policy
        self.registry = registry

    def execute(
        self,
        *,
        job_id: str,
        plan_id: str,
        step_index: int,
        action_id: str,
        payload: Dict[str, Any],
        mode: str = "manual",
        ctx: Optional[dict] = None,
    ) -> ActionResult:
        ctx = ctx or {}
        ctx.setdefault("bus", self.bus)
        ctx.setdefault("artifacts", self.artifacts)
        ctx.setdefault("policy", self.policy)
        ctx.setdefault("mode", mode)
        try:
            impl = self.registry.get_impl(action_id)
        except UnknownAction as exc:
            raise RuntimeError(f"Unknown action implementation: {action_id}") from exc
        result = impl.run(
            payload=payload,
            ctx=ctx,
            job_id=job_id,
            plan_id=plan_id,
            step_index=step_index,
            action_id=action_id,
        )
        if isinstance(result, ActionResult):
            return result
        if isinstance(result, dict):
            return ActionResult(
                ok=bool(result.get("ok", True)),
                artifact_id=result.get("artifact_id"),
                summary=str(result.get("summary", "")),
                meta=result.get("meta"),
            )
        return ActionResult(ok=True, summary="done", meta={"result": result})
