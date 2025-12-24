from __future__ import annotations

from typing import Any, Dict, List
import time

from smolotchi.actions.parse import parse_nmap_xml_up_hosts
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

    def run(
        self,
        plan: Dict[str, Any],
        mode: str,
        max_hosts: int = 16,
        max_steps: int = 80,
    ) -> Dict[str, Any]:
        t0 = time.time()
        out_steps: List[Dict[str, Any]] = []
        self.bus.publish("plan.started", {"id": plan.get("id"), "mode": mode})

        steps = list(plan.get("steps", []))
        expand_hosts = bool(plan.get("expand_hosts", False))
        per_host_actions = list(plan.get("per_host_actions", []))
        discovered_hosts: List[str] = []
        discovery_artifact_id: str | None = None

        i = 0
        while i < len(steps):
            step = steps[i]
            aid = step.get("action_id")
            payload = step.get("payload", {}) or {}
            spec = self.registry.get(aid)
            if not spec:
                out_steps.append({"action_id": aid, "ok": False, "reason": "unknown_action"})
                i += 1
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

            if expand_hosts and aid == "net.host_discovery" and res.artifact_id:
                discovery_artifact_id = res.artifact_id
                art = self.artifacts.get_json(res.artifact_id) or {}
                stdout = str(art.get("stdout") or "")
                discovered_hosts = parse_nmap_xml_up_hosts(stdout)[:max_hosts]
                self.bus.publish(
                    "plan.expand.hosts",
                    {"plan_id": plan.get("id"), "count": len(discovered_hosts)},
                )

                for host in discovered_hosts:
                    for action_id in per_host_actions:
                        if len(steps) >= max_steps:
                            break
                        steps.append({"action_id": action_id, "payload": {"target": host}})
                    if len(steps) >= max_steps:
                        break

            i += 1

        result = {
            "plan_id": plan.get("id"),
            "scope": plan.get("scope"),
            "mode": mode,
            "steps": out_steps,
            "discovered_hosts": discovered_hosts,
            "discovery_artifact_id": discovery_artifact_id,
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
