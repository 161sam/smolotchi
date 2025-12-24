from __future__ import annotations

from typing import Any, Dict, List
import time

from smolotchi.actions.cache import (
    find_fresh_discovery,
    find_fresh_portscan_for_host,
    find_fresh_vuln_for_host_action,
    put_service_fingerprint,
)
from smolotchi.actions.fingerprint import (
    service_fingerprint,
    service_fingerprint_by_key,
)
from smolotchi.actions.parse import parse_nmap_xml_up_hosts
from smolotchi.actions.parse_services import (
    parse_nmap_xml_services,
    summarize_service_keys,
)
from smolotchi.actions.registry import ActionRegistry
from smolotchi.actions.runner import ActionRunner
from smolotchi.actions.summary import build_host_summary
from smolotchi.actions.throttle import (
    decide_multiplier,
    read_cpu_temp_c,
    read_loadavg_1m,
)
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.reports.aggregate import build_aggregate_report


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
        use_cached_portscan: bool = True,
        portscan_ttl_s: int = 900,
        use_cached_vuln: bool = True,
        vuln_ttl_s: int = 1800,
        batch_strategy: str = "phases",
        throttle_cfg: dict | None = None,
        service_map: dict | None = None,
        cache_cfg: dict | None = None,
        invalidation_cfg: dict | None = None,
    ) -> Dict[str, Any]:
        throttle_cfg = throttle_cfg or {}
        cache_cfg = cache_cfg or {}
        invalidation_cfg = invalidation_cfg or {}
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
        current_services_by_host: dict[str, list] = {}
        current_fp_all_by_host: dict[str, str] = {}
        current_fp_bykey_by_host: dict[str, dict[str, str]] = {}
        dirty_keys_by_host: dict[str, set[str]] = {}
        latest_fp_payload_by_host: dict[str, dict] = {}

        def diff_ports(prev: dict, cur: dict) -> dict:
            out = {}
            for key in ("http", "ssh", "smb"):
                a = set((prev or {}).get(key, []) or [])
                b = set((cur or {}).get(key, []) or [])
                if a != b:
                    out[key] = {"prev": sorted(a), "cur": sorted(b)}
            return out

        def vuln_ttl_for_key(key: str) -> int:
            base = int(cache_cfg.get("vuln_ttl_seconds", vuln_ttl_s))
            if key == "http":
                value = int(cache_cfg.get("vuln_ttl_http_seconds", 0))
                return value if value > 0 else base
            if key == "ssh":
                value = int(cache_cfg.get("vuln_ttl_ssh_seconds", 0))
                return value if value > 0 else base
            if key == "smb":
                value = int(cache_cfg.get("vuln_ttl_smb_seconds", 0))
                return value if value > 0 else base
            return base
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

            cache_portscan = None
            if aid == "net.port_scan" and use_cached_portscan:
                host = str(payload.get("target") or "")
                if host:
                    cache_portscan = find_fresh_portscan_for_host(
                        self.artifacts,
                        host=host,
                        ttl_s=portscan_ttl_s,
                    )
                    if cache_portscan:
                        self.bus.publish(
                            "plan.cache.portscan_hit",
                            {
                                "plan_id": plan.get("id"),
                                "host": host,
                                "artifact_id": cache_portscan["artifact_id"],
                                "age_s": int(time.time() - float(cache_portscan["ts"])),
                            },
                        )

                        out_steps.append(
                            {
                                "action_id": aid,
                                "ok": True,
                                "artifact_id": cache_portscan["artifact_id"],
                                "summary": "cache_hit",
                                "meta": {"cache": True},
                            }
                        )

                        services = cache_portscan.get("services", []) or []
                        current_services_by_host[host] = services
                        fp_all = service_fingerprint(services)
                        fp_map = service_fingerprint_by_key(services)
                        current_fp_all_by_host[host] = fp_all
                        current_fp_bykey_by_host[host] = fp_map

                        fp_art_id = put_service_fingerprint(
                            self.artifacts,
                            host=host,
                            services=services,
                            source="portscan_cache",
                        )
                        self.bus.publish(
                            "svc.fp.updated",
                            {
                                "host": host,
                                "fp": fp_all,
                                "fp_by_key": fp_map,
                                "source": "portscan_cache",
                                "artifact_id": fp_art_id,
                            },
                        )
                        fp_payload = self.artifacts.get_json(fp_art_id) or {}
                        latest_fp_payload_by_host[host] = fp_payload
                        dirty = set()
                        if invalidation_cfg.get("enabled", True) and invalidation_cfg.get(
                            "invalidate_on_port_change", True
                        ):
                            prev = None
                            fps = self.artifacts.list(limit=10, kind="svc_fingerprint")
                            for item in fps:
                                if item.id == fp_art_id:
                                    continue
                                data = self.artifacts.get_json(item.id) or {}
                                if data.get("host") == host:
                                    prev = data
                                    break
                            cur_ports = (fp_payload or {}).get("ports_by_key", {}) or {}
                            prev_ports = (prev or {}).get("ports_by_key", {}) or {}
                            changes = diff_ports(prev_ports, cur_ports)
                            if changes:
                                self.bus.publish(
                                    "svc.ports.changed",
                                    {"host": host, "changes": changes},
                                )
                                dirty = set(changes.keys())
                        dirty_keys_by_host[host] = dirty

                        keys = summarize_service_keys(services)
                        injected: List[Dict[str, Any]] = []
                        for key in sorted(keys):
                            for act in service_map.get(key, []):
                                mark = (host, key, act)
                                if mark in already_injected:
                                    continue
                                already_injected.add(mark)
                                fp_map = current_fp_bykey_by_host.get(host, {})
                                fp_key = (
                                    fp_map.get(key) or current_fp_all_by_host.get(host) or ""
                                )
                                injected.append(
                                    {
                                        "action_id": act,
                                        "payload": {
                                            "target": host,
                                            "_svc_key": key,
                                            "_svc_fp": fp_key,
                                        },
                                    }
                                )

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
                                    "source": "portscan_cache",
                                },
                            )

                        time.sleep(max(0, effective_action_ms) / 1000.0)
                        i += 1
                        continue

            if use_cached_vuln and spec.category == "vuln_assess":
                host = str(payload.get("target") or "")
                if host:
                    svc_key = str(payload.get("_svc_key") or "all")
                    expected_fp = current_fp_all_by_host.get(host) or str(
                        payload.get("_svc_fp") or ""
                    )
                    if svc_key in (dirty_keys_by_host.get(host) or set()):
                        self.bus.publish(
                            "plan.cache.vuln_bypass_dirty",
                            {
                                "plan_id": plan.get("id"),
                                "host": host,
                                "svc_key": svc_key,
                                "action_id": spec.id,
                            },
                        )
                        cache_vuln = None
                    else:
                        ttl = vuln_ttl_for_key(svc_key)
                        if expected_fp:
                            cache_vuln = find_fresh_vuln_for_host_action(
                                self.artifacts,
                                host=host,
                                action_id=spec.id,
                                ttl_s=ttl,
                                expected_fp=expected_fp,
                            )
                        else:
                            cache_vuln = None
                    if cache_vuln:
                        self.bus.publish(
                            "plan.cache.vuln_hit",
                            {
                                "plan_id": plan.get("id"),
                                "host": host,
                                "action_id": spec.id,
                                "svc_key": svc_key,
                                "ttl_s": vuln_ttl_for_key(svc_key),
                                "artifact_id": cache_vuln["artifact_id"],
                                "age_s": int(
                                    time.time() - float(cache_vuln["ts"])
                                ),
                            },
                        )

                        out_steps.append(
                            {
                                "action_id": spec.id,
                                "ok": True,
                                "artifact_id": cache_vuln["artifact_id"],
                                "summary": "cache_hit",
                                "meta": {"cache": True},
                            }
                        )

                        time.sleep(max(0, effective_action_ms) / 1000.0)
                        i += 1
                        continue
                    if expected_fp and not cache_vuln and svc_key not in (
                        dirty_keys_by_host.get(host) or set()
                    ):
                        self.bus.publish(
                            "plan.cache.vuln_miss_fp",
                            {
                                "plan_id": plan.get("id"),
                                "host": host,
                                "action_id": spec.id,
                            },
                        )

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

                current_services_by_host[host] = host_services
                fp_all = service_fingerprint(host_services)
                fp_map = service_fingerprint_by_key(host_services)
                current_fp_all_by_host[host] = fp_all
                current_fp_bykey_by_host[host] = fp_map

                fp_art_id = put_service_fingerprint(
                    self.artifacts,
                    host=host,
                    services=host_services,
                    source="live_portscan",
                )
                self.bus.publish(
                    "svc.fp.updated",
                    {
                        "host": host,
                        "fp": fp_all,
                        "fp_by_key": fp_map,
                        "source": "live_portscan",
                        "artifact_id": fp_art_id,
                    },
                )
                fp_payload = self.artifacts.get_json(fp_art_id) or {}
                latest_fp_payload_by_host[host] = fp_payload
                dirty = set()
                if invalidation_cfg.get("enabled", True) and invalidation_cfg.get(
                    "invalidate_on_port_change", True
                ):
                    prev = None
                    fps = self.artifacts.list(limit=10, kind="svc_fingerprint")
                    for item in fps:
                        if item.id == fp_art_id:
                            continue
                        data = self.artifacts.get_json(item.id) or {}
                        if data.get("host") == host:
                            prev = data
                            break
                    cur_ports = (fp_payload or {}).get("ports_by_key", {}) or {}
                    prev_ports = (prev or {}).get("ports_by_key", {}) or {}
                    changes = diff_ports(prev_ports, cur_ports)
                    if changes:
                        self.bus.publish(
                            "svc.ports.changed",
                            {"host": host, "changes": changes},
                        )
                        dirty = set(changes.keys())
                dirty_keys_by_host[host] = dirty

                injected: List[Dict[str, Any]] = []
                for key in sorted(keys):
                    for act in service_map.get(key, []):
                        mark = (host, key, act)
                        if mark in already_injected:
                            continue
                        already_injected.add(mark)
                        fp_key = fp_map.get(key) or fp_all
                        injected.append(
                            {
                                "action_id": act,
                                "payload": {
                                    "target": host,
                                    "_svc_key": key,
                                    "_svc_fp": fp_key,
                                },
                            }
                        )

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
                            "source": "live_portscan",
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
        summary = build_host_summary(result, latest_fp_payload_by_host)
        smeta = self.artifacts.put_json(
            kind="host_summary",
            title=f"Host Summary • {plan.get('id')}",
            payload=summary,
        )
        self.bus.publish(
            "host.summary.created",
            {"plan_id": plan.get("id"), "artifact_id": smeta.id},
        )
        html = build_aggregate_report(
            artifacts=self.artifacts,
            host_summary_artifact_id=smeta.id,
            title="Smolotchi • Aggregate Report",
            bundle_id=None,
        )
        rmeta = self.artifacts.put_file(
            kind="lan_report",
            title=f"Aggregate Report • {plan.get('id')}",
            filename="report.html",
            content=html.encode("utf-8"),
            mimetype="text/html; charset=utf-8",
        )
        self.bus.publish(
            "report.aggregate.created",
            {"plan_id": plan.get("id"), "artifact_id": rmeta.id},
        )
        self.bus.publish(
            "plan.finished",
            {"id": plan.get("id"), "artifact_id": meta.id, "ok": all(s["ok"] for s in out_steps)},
        )
        result["artifact_id"] = meta.id
        result["host_summary_artifact_id"] = smeta.id
        result["aggregate_report_artifact_id"] = rmeta.id
        return result
