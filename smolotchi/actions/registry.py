from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yaml

from .execution import run_action_spec
from .schema import ActionSpec


class UnknownAction(KeyError):
    pass


@dataclass(frozen=True)
class ActionImpl:
    id: str
    run: Callable[..., Any]


class ActionRegistry:
    def __init__(self) -> None:
        self._specs: Dict[str, ActionSpec] = {}
        self._impls: Dict[str, ActionImpl] = {}

    def register(self, spec: ActionSpec) -> None:
        self.register_spec(spec)

    def register_spec(self, spec: ActionSpec) -> None:
        if not spec.id:
            raise ValueError("ActionSpec.id missing")
        self._specs[spec.id] = spec
        if spec.id not in self._impls:
            self._impls[spec.id] = self._default_impl(spec)

    def register_impl(self, action_id: str, run: Callable[..., Any]) -> None:
        if not action_id:
            raise ValueError("action_id missing")
        self._impls[action_id] = ActionImpl(id=action_id, run=run)

    def get(self, action_id: str) -> Optional[ActionSpec]:
        return self._specs.get(action_id)

    def get_spec(self, action_id: str) -> Optional[ActionSpec]:
        return self._specs.get(action_id)

    def get_impl(self, action_id: str) -> ActionImpl:
        try:
            return self._impls[action_id]
        except KeyError as exc:
            raise UnknownAction(action_id) from exc

    def all(self) -> List[ActionSpec]:
        return list(self._specs.values())

    def by_category(self, category: str) -> List[ActionSpec]:
        return [a for a in self._specs.values() if a.category == category]

    def dump(self) -> List[Dict[str, Any]]:
        return [asdict(spec) for spec in self._specs.values()]

    @staticmethod
    def _default_impl(spec: ActionSpec) -> ActionImpl:
        def _run(*, payload: Dict[str, Any], ctx: Optional[dict] = None, **_) -> Any:
            ctx = ctx or {}
            bus = ctx.get("bus")
            artifacts = ctx.get("artifacts")
            policy = ctx.get("policy")
            mode = ctx.get("mode") or "manual"
            if not bus or not artifacts or not policy:
                raise RuntimeError(f"Action context missing for {spec.id}")
            return run_action_spec(
                spec=spec,
                payload=payload,
                mode=mode,
                bus=bus,
                artifacts=artifacts,
                policy=policy,
            )

        return ActionImpl(id=spec.id, run=_run)


def _spec_from_dict(d: Dict[str, Any]) -> ActionSpec:
    return ActionSpec(
        id=str(d["id"]),
        name=str(d.get("name", d["id"])),
        category=str(d.get("category", "network_scan")),  # type: ignore[arg-type]
        description=str(d.get("description", "")),
        tags=list(d.get("tags", [])),
        inputs_schema=dict(d.get("inputs_schema", {})),
        driver=str(d.get("driver", "builtin")),  # type: ignore[arg-type]
        command=list(d.get("command")) if d.get("command") else None,
        timeout_s=int(d.get("timeout_s", 120)),
        produces=list(d.get("produces", ["artifact"])),
        risk=str(d.get("risk", "safe")),  # type: ignore[arg-type]
        requires_confirmation=bool(d.get("requires_confirmation", False)),
        allow_autonomous=bool(d.get("allow_autonomous", False)),
        allowed_scopes=list(d.get("allowed_scopes", [])),
    )


def load_pack(path: str) -> ActionRegistry:
    p = Path(path)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
    actions = data.get("actions", []) if isinstance(data, dict) else []
    reg = ActionRegistry()
    for action in actions:
        if not isinstance(action, dict):
            continue
        reg.register(_spec_from_dict(action))
    return reg
