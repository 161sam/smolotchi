import time
from dataclasses import dataclass
from typing import Optional

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.engines import EngineHealth
from smolotchi.core.jobs import JobRow, JobStore
from smolotchi.core.reports import ReportRenderer


@dataclass
class LanConfig:
    enabled: bool = True
    safe_mode: bool = True
    max_jobs_per_tick: int = 1
    noisy_scripts: list[str] | None = None
    allowlist_scripts: list[str] | None = None


class LanEngine:
    name = "lan"

    def __init__(
        self,
        bus: SQLiteBus,
        cfg: LanConfig,
        artifacts: ArtifactStore,
        jobs: JobStore,
        report_renderer: Optional[ReportRenderer] = None,
        registry=None,
        planner=None,
        plan_runner=None,
        ai_max_hosts: int = 16,
        ai_max_steps: int = 80,
        ai_include_vuln: bool = True,
        ai_batch_strategy: str = "phases",
        ai_throttle: Optional[dict] = None,
        ai_exec: Optional[dict] = None,
        ai_cache: Optional[dict] = None,
        invalidation: Optional[dict] = None,
        report_cfg: Optional[dict] = None,
    ):
        self.bus = bus
        self.cfg = cfg
        self.artifacts = artifacts
        self.jobs = jobs
        self.report_renderer = report_renderer
        self.registry = registry
        self.planner = planner
        self.plan_runner = plan_runner
        self.ai_max_hosts = ai_max_hosts
        self.ai_max_steps = ai_max_steps
        self.ai_include_vuln = ai_include_vuln
        self.ai_batch_strategy = ai_batch_strategy
        self.ai_throttle = ai_throttle or {}
        self.ai_exec = ai_exec or {}
        self.ai_cache = ai_cache or {}
        self.invalidation = invalidation or {}
        self.report_cfg = report_cfg or {}
        self._running = False
        self._active: Optional[JobRow] = None

    def start(self) -> None:
        self._running = True
        self.bus.publish("lan.engine.started", {"safe_mode": self.cfg.safe_mode})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("lan.engine.stopped", {})

    def enqueue(self, job_dict: dict) -> None:
        self.jobs.enqueue(job_dict)
        self.bus.publish(
            "lan.job.enqueued",
            {
                "id": job_dict["id"],
                "kind": job_dict["kind"],
                "scope": job_dict["scope"],
                "note": job_dict.get("note", ""),
            },
        )

    def generate_plan(self, scope: str, note: str = "") -> None:
        if not self.planner:
            self.bus.publish("ai.plan.error", {"reason": "planner_missing"})
            return
        plan = self.planner.generate(
            scope=scope,
            mode="autonomous_safe",
            note=note,
            include_vuln_assess=self.ai_include_vuln,
        )
        payload = {
            "id": plan.id,
            "created_ts": plan.created_ts,
            "mode": plan.mode,
            "scope": plan.scope,
            "steps": [{"action_id": s.action_id, "payload": s.payload} for s in plan.steps],
            "note": plan.note,
            "expand_hosts": True,
            "per_host_actions": ["net.port_scan"],
        }
        meta = self.artifacts.put_json(
            kind="ai_plan",
            title=f"AI Plan • {plan.id}",
            payload=payload,
        )
        self.bus.publish("ai.plan.stored", {"plan_id": plan.id, "artifact_id": meta.id})

    def run_latest_plan_autonomous(self) -> None:
        if not self.plan_runner:
            self.bus.publish("ai.plan.error", {"reason": "plan_runner_missing"})
            return
        plans = self.artifacts.list(limit=50, kind="ai_plan")
        if not plans:
            self.bus.publish("ai.plan.missing", {})
            return
        plan_id = plans[0].id
        plan = self.artifacts.get_json(plan_id)
        if not plan:
            self.bus.publish("ai.plan.missing", {"artifact_id": plan_id})
            return
        res = self.plan_runner.run(
            plan,
            mode="autonomous",
            max_hosts=self.ai_max_hosts,
            max_steps=self.ai_max_steps,
            cooldown_action_ms=int(self.ai_exec.get("cooldown_between_actions_ms", 250)),
            cooldown_host_ms=int(self.ai_exec.get("cooldown_between_hosts_ms", 800)),
            max_retries=int(self.ai_exec.get("max_retries", 1)),
            retry_backoff_ms=int(self.ai_exec.get("retry_backoff_ms", 800)),
            use_cached_discovery=bool(self.ai_cache.get("use_cached_discovery", True)),
            discovery_ttl_s=int(self.ai_cache.get("discovery_ttl_seconds", 600)),
            use_cached_portscan=bool(self.ai_cache.get("use_cached_portscan", True)),
            portscan_ttl_s=int(self.ai_cache.get("portscan_ttl_seconds", 900)),
            use_cached_vuln=bool(self.ai_cache.get("use_cached_vuln", True)),
            vuln_ttl_s=int(self.ai_cache.get("vuln_ttl_seconds", 1800)),
            batch_strategy=self.ai_batch_strategy,
            throttle_cfg=self.ai_throttle,
            cache_cfg={
                "vuln_ttl_seconds": int(self.ai_cache.get("vuln_ttl_seconds", 1800)),
                "vuln_ttl_http_seconds": int(
                    self.ai_cache.get("vuln_ttl_http_seconds", 600)
                ),
                "vuln_ttl_ssh_seconds": int(
                    self.ai_cache.get("vuln_ttl_ssh_seconds", 3600)
                ),
                "vuln_ttl_smb_seconds": int(
                    self.ai_cache.get("vuln_ttl_smb_seconds", 1800)
                ),
            },
            invalidation_cfg={
                "enabled": bool(self.invalidation.get("enabled", True)),
                "invalidate_on_port_change": bool(
                    self.invalidation.get("invalidate_on_port_change", True)
                ),
            },
            report_cfg=self.report_cfg,
            service_map={
                "http": ["vuln.http_basic"],
                "ssh": ["vuln.ssh_basic"],
                "smb": ["vuln.smb_basic"],
            }
            if self.ai_include_vuln
            else {},
        )
        bundle = {
            "job_id": f"ai-{plan.get('id')}",
            "kind": "ai_autonomous_safe",
            "scope": plan.get("scope"),
            "created_ts": time.time(),
            "plan_artifact_id": plan_id,
            "plan_run_artifact_id": res.get("artifact_id"),
            "host_summary_artifact_id": res.get("host_summary_artifact_id"),
            "reports": {
                "html": {
                    "artifact_id": res.get("aggregate_report_artifact_id"),
                    "title": f"Aggregate Report • {plan.get('id')}",
                },
                "md": {
                    "artifact_id": res.get("aggregate_report_md_artifact_id"),
                    "title": f"Aggregate Report (MD) • {plan.get('id')}",
                },
                "json": {
                    "artifact_id": res.get("aggregate_report_json_artifact_id"),
                    "title": f"Aggregate Report (JSON) • {plan.get('id')}",
                },
                "diff": {
                    "html": {
                        "artifact_id": res.get("diff_report_html_artifact_id"),
                        "title": "Host Diff (HTML)",
                    },
                    "md": {
                        "artifact_id": res.get("diff_report_md_artifact_id"),
                        "title": "Host Diff (MD)",
                    },
                    "json": {
                        "artifact_id": res.get("diff_report_json_artifact_id"),
                        "title": "Host Diff (JSON)",
                    },
                },
            },
            "diff_summary": {
                "artifact_id": res.get("diff_report_json_artifact_id"),
                "html_artifact_id": res.get("diff_report_html_artifact_id"),
                "changed_hosts_count": res.get("diff_changed_hosts_count", 0),
                "changed_hosts": res.get("diff_changed_hosts", []),
            },
            "diff_badges": res.get("diff_badges") or {},
        }
        bmeta = self.artifacts.put_json(
            kind="lan_bundle",
            title=f"Bundle • {bundle['job_id']}",
            payload=bundle,
        )
        self.bus.publish(
            "ai.autonomous.finished",
            {"bundle_id": bmeta.id, "plan_run_artifact_id": res.get("artifact_id")},
        )

    def tick(self) -> None:
        if not self._running or not self.cfg.enabled:
            return

        if self._active is None:
            self._active = self.jobs.pop_next()
            if self._active:
                self.bus.publish(
                    "lan.job.started",
                    {
                        "id": self._active.id,
                        "kind": self._active.kind,
                        "scope": self._active.scope,
                    },
                )

        if self._active is not None:
            try:
                result = {
                    "job": {
                        "id": self._active.id,
                        "kind": self._active.kind,
                        "scope": self._active.scope,
                        "note": self._active.note,
                    },
                    "summary": "stub result (persist queue v0.0.6)",
                    "ts": time.time(),
                }

                meta_json = self.artifacts.put_json(
                    kind="lan_result",
                    title=f"LAN {self._active.kind} • {self._active.scope}",
                    payload=result,
                )
                report_meta = None
                if self.report_renderer is not None:
                    html_bytes = self.report_renderer.render_lan_result(
                        title=f"LAN {self._active.kind} • {self._active.scope}",
                        result=result,
                    )
                    report_meta = self.artifacts.put_file(
                        kind="lan_report",
                        title=f"Report • {self._active.id}",
                        filename="report.html",
                        content=html_bytes,
                        mimetype="text/html; charset=utf-8",
                    )

                bundle = {
                    "job_id": self._active.id,
                    "kind": self._active.kind,
                    "scope": self._active.scope,
                    "note": self._active.note,
                    "created_ts": time.time(),
                    "result_json": {
                        "artifact_id": meta_json.id,
                        "path": meta_json.path,
                    },
                    "report_html": {
                        "artifact_id": report_meta.id,
                        "path": report_meta.path,
                    }
                    if report_meta
                    else None,
                }

                bundle_meta = self.artifacts.put_json(
                    kind="lan_bundle",
                    title=f"Bundle • {self._active.id}",
                    payload=bundle,
                )

                self.bus.publish(
                    "lan.job.progress", {"id": self._active.id, "pct": 100}
                )
                self.bus.publish(
                    "lan.job.finished",
                    {
                        "id": self._active.id,
                        "result": {
                            "artifact_id": meta_json.id,
                            "artifact_path": meta_json.path,
                            "report_artifact_id": report_meta.id if report_meta else None,
                            "report_path": report_meta.path if report_meta else None,
                            "bundle_artifact_id": bundle_meta.id,
                        },
                    },
                )
                self.jobs.mark_done(self._active.id)
            except Exception as ex:
                self.bus.publish(
                    "lan.job.failed", {"id": self._active.id, "err": str(ex)}
                )
                self.jobs.mark_failed(self._active.id, note=str(ex))
            finally:
                self._active = None

    def health(self) -> EngineHealth:
        if not self.cfg.enabled:
            return EngineHealth(name=self.name, ok=True, detail="disabled")
        queued = self.jobs.list(limit=1, status="queued")
        detail = (
            "running queued="
            f"{'yes' if queued else 'no'} active={'yes' if self._active else 'no'}"
            if self._running
            else "stopped"
        )
        return EngineHealth(name=self.name, ok=self._running, detail=detail)
