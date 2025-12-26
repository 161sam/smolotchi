from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
import subprocess
import time

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.policy import Policy
from .schema import ActionSpec


@dataclass
class ActionResult:
    ok: bool
    artifact_id: Optional[str] = None
    summary: str = ""
    meta: Dict[str, Any] | None = None


def run_action_spec(
    *,
    spec: ActionSpec,
    payload: Dict[str, Any],
    mode: str,
    bus: SQLiteBus,
    artifacts: ArtifactStore,
    policy: Policy,
) -> ActionResult:
    bus.publish(
        "action.started", {"id": spec.id, "mode": mode, "category": spec.category}
    )

    if not policy.category_allowed(spec.category):
        bus.publish("action.blocked", {"id": spec.id, "reason": "category_blocked"})
        return ActionResult(
            ok=False,
            summary="blocked by policy",
            meta={"reason": "category_blocked"},
        )

    if mode == "autonomous" and not (
        spec.allow_autonomous and policy.autonomous_allowed(spec.category)
    ):
        bus.publish(
            "action.blocked", {"id": spec.id, "reason": "autonomous_not_allowed"}
        )
        return ActionResult(
            ok=False,
            summary="autonomous not allowed",
            meta={"reason": "autonomous_not_allowed"},
        )

    target = payload.get("scope") or payload.get("target")
    if target and not policy.scope_allowed(str(target)):
        bus.publish(
            "action.blocked",
            {"id": spec.id, "reason": "scope_not_allowed", "target": target},
        )
        return ActionResult(
            ok=False,
            summary="scope not allowed",
            meta={"reason": "scope_not_allowed"},
        )

    if spec.requires_confirmation and mode != "manual":
        bus.publish(
            "action.blocked", {"id": spec.id, "reason": "confirmation_required"}
        )
        return ActionResult(
            ok=False,
            summary="confirmation required",
            meta={"reason": "confirmation_required"},
        )

    if spec.driver == "external_stub":
        out = {
            "note": "external_stub - not implemented in Smolotchi default build",
            "payload": payload,
        }
        meta = artifacts.put_json(
            kind="action_stub",
            title=f"{spec.name} (stub)",
            payload=out,
        )
        bus.publish(
            "action.finished",
            {"id": spec.id, "ok": True, "artifact_id": meta.id, "stub": True},
        )
        return ActionResult(
            ok=True,
            artifact_id=meta.id,
            summary="stub recorded",
            meta={"stub": True},
        )

    if spec.driver == "command":
        if not spec.command:
            return ActionResult(ok=False, summary="no command configured", meta={})
        tool = spec.command[0]
        if tool not in policy.allowed_tools:
            bus.publish(
                "action.blocked",
                {"id": spec.id, "reason": "tool_not_allowed", "tool": tool},
            )
            return ActionResult(
                ok=False,
                summary="tool not allowed",
                meta={"tool": tool},
            )

        cmd = [c.format(**payload) for c in spec.command]
        t0 = time.time()
        try:
            cp = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=spec.timeout_s,
            )
            dur = time.time() - t0
            res = {
                "spec": {
                    "id": spec.id,
                    "name": spec.name,
                    "category": spec.category,
                },
                "payload": payload,
                "cmd": cmd,
                "returncode": cp.returncode,
                "stdout": cp.stdout[-20000:],
                "stderr": cp.stderr[-20000:],
                "duration_s": dur,
                "ts": time.time(),
            }
            meta = artifacts.put_json(
                kind="action_run",
                title=spec.name,
                payload=res,
            )
            ok = cp.returncode == 0
            bus.publish(
                "action.finished", {"id": spec.id, "ok": ok, "artifact_id": meta.id}
            )
            return ActionResult(
                ok=ok,
                artifact_id=meta.id,
                summary="done",
                meta={"rc": cp.returncode},
            )
        except subprocess.TimeoutExpired:
            bus.publish(
                "action.finished", {"id": spec.id, "ok": False, "timeout": True}
            )
            return ActionResult(
                ok=False,
                summary="timeout",
                meta={"timeout": True},
            )

    meta = artifacts.put_json(
        kind="action_builtin", title=spec.name, payload={"payload": payload}
    )
    bus.publish("action.finished", {"id": spec.id, "ok": True, "artifact_id": meta.id})
    return ActionResult(
        ok=True, artifact_id=meta.id, summary="builtin placeholder", meta={}
    )
