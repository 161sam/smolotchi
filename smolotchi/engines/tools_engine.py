import subprocess
import time

from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.core.engines import EngineHealth
from smolotchi.core.jobs import JobRow, JobStore
from smolotchi.core.policy import evaluate_tool_action


class ToolsEngine:
    name = "tools"

    def __init__(
        self,
        bus: SQLiteBus,
        artifacts: ArtifactStore,
        jobstore: JobStore,
        config: ConfigStore,
    ):
        self.bus = bus
        self.artifacts = artifacts
        self.jobstore = jobstore
        self.config = config
        self._running = True

    def start(self) -> None:
        self._running = True
        self.bus.publish("tools.engine.start", {"ts": time.time()})

    def stop(self) -> None:
        self._running = False
        self.bus.publish("tools.engine.stop", {"ts": time.time()})

    def tick(self) -> None:
        if not self._running:
            return
        self._release_approved_blocks()
        job = self.jobstore.pop_next_filtered(include_prefixes=["scan."])
        if not job:
            return
        self.bus.publish("tools.job.started", {"id": job.id, "kind": job.kind})
        ok = False
        err = ""
        try:
            action = job.kind
            tool = self._tool_for_job(job.kind)
            if tool:
                decision = self._evaluate_policy(tool=tool, job=job)
                approved = False
                if decision.requires_approval:
                    request_id = self._extract_stage_request_id(job.note)
                    if self._has_approval(request_id):
                        approved = True
                        self.bus.publish(
                            "policy.approved",
                            {
                                "ts": time.time(),
                                "job_id": job.id,
                                "action": action,
                                "request_id": request_id,
                            },
                        )
                    else:
                        request_id = self._ensure_stage_request(job=job, action_id=action)
                        note = f"blocked: approval required for {action} stage_req:{request_id}"
                        self.jobstore.mark_blocked(job.id, note=note)
                        self.bus.publish(
                            "policy.approval.required",
                            {
                                "ts": time.time(),
                                "job_id": job.id,
                                "action": action,
                                "request_id": request_id,
                                "reason": decision.reason,
                            },
                        )
                        return
                if not decision.ok and not approved:
                    err = f"blocked by policy: {decision.reason}"
                    self.jobstore.mark_failed(job.id, err)
                    self.bus.publish(
                        "policy.blocked",
                        {
                            "ts": time.time(),
                            "job_id": job.id,
                            "action": action,
                            "reason": decision.reason,
                        },
                    )
                    return
            if job.kind == "scan.nmap":
                ok = self._run_nmap(job)
            elif job.kind == "scan.bettercap":
                ok = self._run_bettercap(job)
            else:
                err = f"unknown kind {job.kind}"
                self.jobstore.mark_failed(job.id, err)
        except Exception as exc:
            err = str(exc)
            self.jobstore.mark_failed(job.id, err)
        else:
            if ok:
                self.jobstore.mark_done(job.id)
            elif not err:
                self.jobstore.mark_failed(job.id, "tool failed")
        finally:
            self.bus.publish("tools.job.finished", {"id": job.id, "ok": ok, "err": err})

    def _run_nmap(self, job: JobRow) -> bool:
        cmd = ["nmap", "-sn", "-oX", "-", job.scope]
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        payload = {
            "job_id": job.id,
            "ts": start,
            "scope": job.scope,
            "cmd": " ".join(cmd),
            "stdout": result.stdout,
            "stderr": result.stderr,
            "rc": result.returncode,
        }
        result_meta = self.artifacts.put_json(
            kind="lan_result",
            title=f"nmap {job.scope}",
            payload=payload,
        )
        self._store_bundle(job, result_meta.id, ok=result.returncode == 0)
        return result.returncode == 0

    def _run_bettercap(self, job: JobRow) -> bool:
        cmd = [
            "bettercap",
            "-eval",
            f"set net.probe.targets {job.scope}; net.probe on; sleep 10; exit",
        ]
        start = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        payload = {
            "job_id": job.id,
            "ts": start,
            "scope": job.scope,
            "cmd": " ".join(cmd),
            "stdout": result.stdout[-8000:],
            "stderr": result.stderr[-8000:],
            "rc": result.returncode,
        }
        result_meta = self.artifacts.put_json(
            kind="lan_result",
            title=f"bettercap {job.scope}",
            payload=payload,
        )
        self._store_bundle(job, result_meta.id, ok=result.returncode == 0)
        return result.returncode == 0

    def _store_bundle(self, job: JobRow, result_id: str, ok: bool) -> None:
        bundle = {
            "job_id": job.id,
            "kind": job.kind,
            "scope": job.scope,
            "note": job.note,
            "created_ts": time.time(),
            "result_json": {"artifact_id": result_id},
        }
        bundle_meta = self.artifacts.put_json(
            kind="lan_bundle",
            title=f"Bundle • {job.id}",
            payload=bundle,
        )
        self.artifacts.put_json(
            kind="lan_job_result",
            title=f"lan job result {job.id}",
            payload={
                "ts": time.time(),
                "job_id": job.id,
                "bundle_id": bundle_meta.id,
                "report_id": None,
                "ok": ok,
            },
        )

    def _tool_for_job(self, kind: str) -> str | None:
        if kind == "scan.nmap":
            return "nmap"
        if kind == "scan.bettercap":
            return "bettercap"
        if kind == "scan.masscan":
            return "masscan"
        return None

    def _evaluate_policy(self, tool: str, job: JobRow):
        cfg = self.config.get()
        policy_cfg = {}
        if cfg and getattr(cfg, "policy", None):
            policy_cfg = vars(cfg.policy)
        return evaluate_tool_action(
            tool=tool,
            job_kind=job.kind,
            scope=job.scope,
            cfg_policy=policy_cfg,
        )

    def _extract_stage_request_id(self, note: str | None) -> str | None:
        if not note:
            return None
        cleaned = note.replace("(", " ").replace(")", " ")
        for part in cleaned.split():
            if part.startswith("stage_req:"):
                return part.split("stage_req:", 1)[1].strip()
            if part.startswith("request_id="):
                return part.split("request_id=", 1)[1].strip()
            if part.startswith("req:"):
                return part.split("req:", 1)[1].strip()
        return None

    def _has_approval(self, request_id: str | None) -> bool:
        if not request_id:
            return False
        return (
            self.artifacts.find_latest_stage_approval_for_request(request_id)
            is not None
        )

    def _ensure_stage_request(self, job: JobRow, action_id: str) -> str:
        existing = self._extract_stage_request_id(job.note)
        if existing:
            return existing
        payload = {
            "job_id": job.id,
            "action_id": action_id,
            "scope": job.scope,
            "reason": f"approval required for {action_id}",
            "ts": time.time(),
        }
        meta = self.artifacts.put_json(
            kind="ai_stage_request",
            title=f"AI Stage Request {action_id}",
            payload=payload,
            tags=["ai", "stage", "request", "policy"],
            meta={"job_id": job.id, "action_id": action_id},
        )
        return meta.id

    def _release_approved_blocks(self) -> None:
        blocked = self.jobstore.list(limit=50, status="blocked")
        for job in blocked:
            if not job.kind.startswith("scan."):
                continue
            request_id = self._extract_stage_request_id(job.note)
            if not request_id or not self._has_approval(request_id):
                continue
            self.jobstore.mark_queued(
                job.id, note=f"approved: stage_req:{request_id}"
            )
            self.bus.publish(
                "policy.approved",
                {
                    "ts": time.time(),
                    "job_id": job.id,
                    "action": job.kind,
                    "request_id": request_id,
                },
            )

    def health(self) -> EngineHealth:
        return EngineHealth(name="tools", ok=self._running, detail="running")
