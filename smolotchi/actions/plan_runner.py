from __future__ import annotations

from typing import Any, Dict, List
import time

from smolotchi.actions.cache import find_fresh_discovery
from smolotchi.actions.parse import parse_nmap_xml_up_hosts
from smolotchi.actions.parse_services import (
    parse_nmap_xml_services,
    summarize_service_keys,
)
from smolotchi.actions.registry import ActionRegistry
from smolotchi.actions.runner import ActionRunner
from smolotchi.actions.throttle import (
    decide_multiplier,
    read_cpu_temp_c,
    read_loadavg_1m,
)
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

    @staticmethod
    def _build_batched_steps(
        hosts: List[str],
        per_host_actions: List[str],
        strategy: str,
    ) -> List[Dict[str, Any]]:
        steps: List[Dict[str, Any]] = []
        if strategy == "per_host":
            for host in hosts:
                for action_id in per_host_actions:
                    steps.append({"action_id": action_id, "payload": {"target": host}})
            return steps

        port_actions = [a for a in per_host_actions if a.startswith("net.")]
        assess_actions = [a for a in per_host_actions if not a.startswith("net.")]
        for action_id in port_actions:
            for host in hosts:
                steps.append({"action_id": action_id, "payload": {"target": host}})
        for action_id in assess_actions:
            for host in hosts:
                steps.append({"action_id": action_id, "payload": {"target": host}})
        return steps

    def run(
        self,
        plan: Dict[str, Any],
        mode: str,
        max_hosts: int = 16,
        max_steps: int = 80,
        cooldown_action_ms: int = 250,
        cooldown_host_ms: int = 800,
        max_retries: int = 1,
        retry_backoff_ms: int = 800,
        use_cached_discovery: bool = True,
        discovery_ttl_s: int = 600,
        batch_strategy: str = "phases",
        throttle_cfg: dict | None = None,
        service_map: dict | None = None,
    ) -> Dict[str, Any]:
        throttle_cfg = throttle_cfg or {}
        if service_map is None:
            service_map = {
                "http": ["vuln.http_basic"],
                "ssh": ["vuln.ssh_basic"],
                "smb": ["vuln.smb_basic"],
            }
        t0 = time.time()
        out_steps: List[Dict[str, Any]] = []
        self.bus.publish("plan.started", {"id": plan.get("id"), "mode": mode})

        steps = list(plan.get("steps", []))
        expand_hosts = bool(plan.get("expand_hosts", False))
        per_host_actions = list(plan.get("per_host_actions", []))
        discovered_hosts: List[str] = []
        discovery_artifact_id: str | None = None

        if expand_hosts and use_cached_discovery:
            cached = find_fresh_discovery(self.artifacts, ttl_s=discovery_ttl_s)
            if cached and cached.get("hosts"):
                discovered_hosts = list(cached["hosts"])[:max_hosts]
                discovery_artifact_id = cached["artifact_id"]
                self.bus.publish(
                    "plan.expand.cache_hit",
                    {
                        "plan_id": plan.get("id"),
                        "count": len(discovered_hosts),
                        "artifact_id": discovery_artifact_id,
                    },
                )
                steps = [s for s in steps if s.get("action_id") != "net.host_discovery"]

        if discovered_hosts and expand_hosts:
            extra = self._build_batched_steps(
                discovered_hosts, per_host_actions, batch_strategy
            )
            for step in extra:
                if len(steps) >= max_steps:
                    break
                steps.append(step)

        already_injected = set()
        i = 0
        last_host = None
        while i < len(steps):
            step = steps[i]
            aid = step.get("action_id")
            payload = step.get("payload", {}) or {}
            spec = self.registry.get(aid)
            if not spec:
                out_steps.append({"action_id": aid, "ok": False, "reason": "unknown_action"})
                i += 1
                continue

            load1 = read_loadavg_1m()
            temp_c = read_cpu_temp_c()
            multiplier = 1.0
            reason = "ok"
            if throttle_cfg and throttle_cfg.get("enabled", True):
                class ThrottleCfg:
                    pass

                cfg_obj = ThrottleCfg()
                for key, value in throttle_cfg.items():
                    setattr(cfg_obj, key, value)
                decision = decide_multiplier(cfg_obj, load1, temp_c)
                multiplier = decision.multiplier
                reason = decision.reason

            effective_action_ms = int(cooldown_action_ms * multiplier)
            effective_host_ms = int(cooldown_host_ms * multiplier)
            min_cd = int(throttle_cfg.get("min_cooldown_ms", 150)) if throttle_cfg else 150
            max_cd = (
                int(throttle_cfg.get("max_cooldown_ms", 5000)) if throttle_cfg else 5000
            )
            effective_action_ms = max(min_cd, min(max_cd, effective_action_ms))
            effective_host_ms = max(min_cd, min(max_cd, effective_host_ms))
            self.bus.publish(
                "plan.throttle",
                {
                    "plan_id": plan.get("id"),
                    "load1": load1,
                    "temp_c": temp_c,
                    "mult": multiplier,
                    "reason": reason,
                    "action_ms": effective_action_ms,
                    "host_ms": effective_host_ms,
                },
            )

            current_host = payload.get("target") or payload.get("host")
            if current_host and last_host and current_host != last_host:
                time.sleep(max(0, effective_host_ms) / 1000.0)
            last_host = current_host if current_host else last_host

            attempt = 0
            res = None
            while True:
                attempt += 1
                res = self.runner.run(spec, payload, mode=mode)
                if res.ok or attempt > max_retries:
                    break
                self.bus.publish(
                    "action.retry",
                    {"id": spec.id, "attempt": attempt, "backoff_ms": retry_backoff_ms},
                )
                time.sleep(max(0, retry_backoff_ms) / 1000.0)
            out_steps.append(
                {
                    "action_id": aid,
                    "ok": res.ok,
                    "artifact_id": res.artifact_id,
                    "summary": res.summary,
                    "meta": res.meta or {},
                }
            )

            if aid == "net.port_scan" and res and res.artifact_id:
                art = self.artifacts.get_json(res.artifact_id) or {}
                stdout = str(art.get("stdout") or "")
                svc_by_host = parse_nmap_xml_services(stdout)

                host = str(payload.get("target") or "")
                host_services = svc_by_host.get(host, [])
                keys = summarize_service_keys(host_services)

                injected: List[Dict[str, Any]] = []
                for key in sorted(keys):
                    for act in service_map.get(key, []):
                        mark = (host, key, act)
                        if mark in already_injected:
                            continue
                        already_injected.add(mark)
                        injected.append({"action_id": act, "payload": {"target": host}})

                if injected:
                    insert_at = i + 1
                    for injected_step in reversed(injected):
                        if len(steps) >= max_steps:
                            break
                        steps.insert(insert_at, injected_step)
                    self.bus.publish(
                        "plan.expand.services",
                        {
                            "plan_id": plan.get("id"),
                            "host": host,
                            "keys": sorted(list(keys)),
                            "injected": [x["action_id"] for x in injected],
                        },
                    )

            if expand_hosts and aid == "net.host_discovery" and res.artifact_id:
                if not discovered_hosts:
                    self.bus.publish("plan.expand.cache_miss", {"plan_id": plan.get("id")})
                discovery_artifact_id = res.artifact_id
                art = self.artifacts.get_json(res.artifact_id) or {}
                stdout = str(art.get("stdout") or "")
                discovered_hosts = parse_nmap_xml_up_hosts(stdout)[:max_hosts]
                self.bus.publish(
                    "plan.expand.hosts",
                    {"plan_id": plan.get("id"), "count": len(discovered_hosts)},
                )

                extra = self._build_batched_steps(
                    discovered_hosts, per_host_actions, batch_strategy
                )
                for step in extra:
                    if len(steps) >= max_steps:
                        break
                    steps.append(step)

            time.sleep(max(0, effective_action_ms) / 1000.0)
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
