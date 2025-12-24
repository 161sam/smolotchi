from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .schema import ActionSpec


class ActionRegistry:
    def __init__(self) -> None:
        self._actions: Dict[str, ActionSpec] = {}

    def register(self, spec: ActionSpec) -> None:
        if not spec.id:
            raise ValueError("ActionSpec.id missing")
        self._actions[spec.id] = spec

    def get(self, action_id: str) -> Optional[ActionSpec]:
        return self._actions.get(action_id)

    def all(self) -> List[ActionSpec]:
        return list(self._actions.values())

    def by_category(self, category: str) -> List[ActionSpec]:
        return [a for a in self._actions.values() if a.category == category]

    def dump(self) -> List[Dict[str, Any]]:
        return [asdict(spec) for spec in self._actions.values()]


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
