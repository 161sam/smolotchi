from __future__ import annotations

import argparse
import logging
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from smolotchi.actions.plan_runner import PlanRunner
from smolotchi.actions.planners.ai_planner import AIPlanner
from smolotchi.actions.registry import ActionRegistry, load_pack
from smolotchi.actions.runner import ActionRunner
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.config import ConfigStore
from smolotchi.core.jobs import JobStore
from smolotchi.core.policy import Policy


@dataclass
class WorkerState:
    running: bool = False
    last_tick: float = 0.0
    current_plan_artifact_id: Optional[str] = None
    current_plan_id: Optional[str] = None
    current_job_id: Optional[str] = None
    last_error: Optional[str] = None


class AIWorker:
    """
    Single-thread worker:
    - listens for ui.ai.run_plan events
    - loads ai_plan artifact
    - executes via PlanRunner
    - emits health ticks
    """

    def __init__(
        self,
        *,
        bus: SQLiteBus,
        registry: ActionRegistry,
        artifacts: ArtifactStore,
        jobstore: JobStore,
        runner: ActionRunner | None = None,
        poll_interval_s: float = 1.0,
    ) -> None:
        self.bus = bus
        self.registry = registry
        self.artifacts = artifacts
        self.jobstore = jobstore
        self.runner = runner
        self.poll_interval_s = poll_interval_s

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.state = WorkerState()
        self.watchdog_s = float(os.environ.get("SMO_AI_WATCHDOG_S", "300"))
        self._last_progress_by_job: dict[str, float] = {}
        self.log = logging.getLogger("smolotchi.ai.worker")
        self._resume_re = re.compile(r"\bresume_from:(\d+)\b")
        self._stage_req_re = re.compile(r"\bstage_req:([a-zA-Z0-9_-]+)\b")

    def _extract_req_id(self, note: str) -> Optional[str]:
        note = note or ""
        for part in note.split():
            if part.startswith("req:"):
                return part.split("req:", 1)[1].strip()
        return None

    def _extract_resume_from(self, note: str) -> Optional[int]:
        if not note:
            return None
        match = self._resume_re.search(note)
        if not match:
            return None
        return int(match.group(1))

    def _extract_stage_req(self, note: str) -> Optional[str]:
        if not note:
            return None
        match = self._stage_req_re.search(note)
        if not match:
            return None
        return match.group(1)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="smolotchi-ai-worker",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)

    def _loop(self) -> None:
        self.state.running = True
        self.bus.publish("ai.worker.started", {"ts": time.time()})
        self.log.info("AI worker started")

        while not self._stop.is_set():
            self._tick()
            time.sleep(self.poll_interval_s)

        self.state.running = False
        self.bus.publish("ai.worker.stopped", {"ts": time.time()})
        self.log.info("AI worker stopped")

    def run_once(self) -> None:
        self._tick()

    def _tick(self) -> None:
        try:
            self.state.last_tick = time.time()
            self.bus.publish("ai.worker.tick", {"ts": self.state.last_tick})

            ai_evts = self.bus.tail(limit=100, topic_prefix="ai.")
            for event in ai_evts:
                payload = event.payload or {}
                jid = payload.get("job_id")
                if jid and event.topic in (
                    "ai.action.started",
                    "ai.action.done",
                    "ai.plan.started",
                ):
                    self._last_progress_by_job[str(jid)] = float(
                        event.ts or time.time()
                    )

            running = [
                j
                for j in self.jobstore.list(limit=10, status="running")
                if getattr(j, "kind", "") == "ai_plan"
            ]
            now = time.time()
            for job in running:
                jid = job.id
                last = self._last_progress_by_job.get(
                    jid, float(getattr(job, "updated_ts", 0.0) or 0.0)
                )
                if last and (now - last) > self.watchdog_s:
                    ok = False
                    try:
                        ok = self.jobstore.reset_running(jid)
                    except Exception:
                        ok = False
                    self.bus.publish(
                        "ai.worker.watchdog.reset",
                        {"job_id": jid, "ok": ok, "age_s": round(now - last, 1)},
                    )
                    self.log.warning(
                        "watchdog reset job_id=%s age_s=%s ok=%s",
                        jid,
                        round(now - last, 1),
                        ok,
                    )

            blocked = [
                j
                for j in self.jobstore.list(limit=20, status="blocked")
                if getattr(j, "kind", "") == "ai_plan"
            ]
            approved_requests = self._approved_stage_request_ids()
            for job in blocked:
                stage_req = self._approved_stage_request_for_job(
                    job.id, approved_requests
                )
                if stage_req:
                    resume_from = stage_req.get("step_index")
                    stage_req_id = stage_req.get("request_id")
                    try:
                        note = "approval granted"
                        if resume_from:
                            note = f"{note} resume_from:{resume_from}"
                        if stage_req_id:
                            note = f"{note} stage_req:{stage_req_id}"
                        self.jobstore.mark_queued(job.id, note=note)
                    except Exception:
                        self.log.debug("job %s: mark_queued failed", job.id)
                    self.bus.publish(
                        "ai.worker.job.unblocked",
                        {"job_id": job.id, "ts": time.time()},
                    )

            queued = self.jobstore.list(limit=20, status="queued")
            queued = [j for j in queued if getattr(j, "kind", "") == "ai_plan"]
            queued = sorted(queued, key=lambda j: j.created_ts)

            for job in queued:
                if getattr(job, "status", "") == "cancelled":
                    continue

                self._process_job(job)
                break

        except Exception as exc:
            self.state.last_error = str(exc)
            self.bus.publish("ai.worker.error", {"error": str(exc), "ts": time.time()})
            self.log.exception("worker tick failed: %s", exc)

    def _approved_stage_request_ids(self) -> set[str]:
        approvals = self.artifacts.list(limit=200, kind="ai_stage_approval")
        approved: set[str] = set()
        for approval in approvals:
            doc = self.artifacts.get_json(approval.id) or {}
            rid = doc.get("request_id")
            if rid:
                approved.add(str(rid))
        return approved

    def _approved_stage_request_for_job(
        self, job_id: str, approved_requests: set[str]
    ) -> Optional[dict]:
        if not approved_requests:
            return None
        requests = self.artifacts.list(limit=200, kind="ai_stage_request")
        for req in requests:
            doc = self.artifacts.get_json(req.id) or {}
            if str(doc.get("job_id")) != str(job_id):
                continue
            if str(req.id) in approved_requests:
                doc = dict(doc)
                doc["request_id"] = req.id
                return doc
        return None

    def _process_job(self, job) -> None:
        job_id = job.id
        try:
            req_id = self._extract_req_id(getattr(job, "note", "") or "")
            if not req_id:
                self.jobstore.mark_failed(
                    job_id,
                    note="missing req:<artifact_id> in job.note",
                )
                self.bus.publish(
                    "ai.worker.job_failed",
                    {"job_id": job_id, "error": "missing run request"},
                )
                self.log.error("job %s failed: missing run request", job_id)
                return

            req = self.artifacts.get_json(req_id)
            if not req:
                self.jobstore.mark_failed(
                    job_id,
                    note=f"run request artifact missing: {req_id}",
                )
                self.bus.publish(
                    "ai.worker.job_failed",
                    {"job_id": job_id, "error": "run request missing"},
                )
                self.log.error(
                    "job %s failed: run request missing req_id=%s", job_id, req_id
                )
                return

            plan_artifact_id = (req.get("plan_artifact_id") or "").strip()
            scope = (req.get("scope") or "").strip()
            note = req.get("note") or ""
            resume_from = self._extract_resume_from(getattr(job, "note", "") or "")

            try:
                self.jobstore.mark_running(job_id)
            except Exception:
                self.log.debug("job %s: mark_running failed", job_id)

            self.bus.publish(
                "ai.worker.dequeue",
                {"job_id": job_id, "req_id": req_id, "ts": time.time()},
            )
            self.log.info(
                "job %s dequeued req_id=%s plan_artifact_id=%s",
                job_id,
                req_id,
                plan_artifact_id or "none",
            )

            if plan_artifact_id:
                self._run_plan_artifact(
                    plan_artifact_id,
                    job_id=job_id,
                    start_step_index=resume_from or 1,
                )
            else:
                planner = AIPlanner(
                    self.bus,
                    self.registry,
                    seed=req.get("seed"),
                    artifacts=self.artifacts,
                )
                plan = planner.generate(
                    scope=scope or "10.0.10.0/24",
                    mode="autonomous_safe",
                    note=note,
                )
                runner = PlanRunner(
                    bus=self.bus,
                    registry=self.registry,
                    jobstore=self.jobstore,
                    artifacts=self.artifacts,
                    runner=self.runner,
                )
                self._run_plan_object(
                    plan,
                    runner,
                    job_id=job_id,
                    start_step_index=resume_from or 1,
                )
        except Exception as exc:
            self.jobstore.mark_failed(job_id, note=str(exc))
            self.bus.publish(
                "ai.worker.job_failed",
                {"job_id": job_id, "error": str(exc)},
            )
            self.log.exception("job %s failed: %s", job_id, exc)

    def _run_plan_artifact(
        self,
        plan_artifact_id: str,
        *,
        job_id: str,
        start_step_index: int = 1,
    ) -> None:
        plan_doc = self.artifacts.get_json(plan_artifact_id)
        if not plan_doc:
            self.jobstore.mark_failed(
                job_id,
                note=f"plan artifact missing: {plan_artifact_id}",
            )
            self.bus.publish(
                "ai.worker.plan_missing",
                {"artifact_id": plan_artifact_id, "job_id": job_id},
            )
            self.log.error(
                "job %s failed: plan artifact missing %s",
                job_id,
                plan_artifact_id,
            )
            return

        class _Plan:
            pass

        plan = _Plan()
        plan.id = plan_doc.get("id")
        plan.mode = plan_doc.get("mode")
        plan.scope = plan_doc.get("scope")
        plan.note = plan_doc.get("note", "")
        plan.seed = plan_doc.get("seed")
        plan.steps = []

        for step in plan_doc.get("steps") or []:
            class _Step:
                pass

            step_obj = _Step()
            step_obj.action_id = step.get("action_id")
            step_obj.payload = step.get("payload") or {}
            step_obj.why = step.get("why") or []
            step_obj.score = step.get("score") or 0.0
            plan.steps.append(step_obj)

        runner = PlanRunner(
            bus=self.bus,
            registry=self.registry,
            jobstore=self.jobstore,
            artifacts=self.artifacts,
            runner=self.runner,
        )

        self._run_plan_object(
            plan,
            runner,
            plan_artifact_id=plan_artifact_id,
            job_id=job_id,
            start_step_index=start_step_index,
        )

    def _run_plan_object(
        self,
        plan,
        runner: PlanRunner,
        *,
        plan_artifact_id: Optional[str] = None,
        job_id: str,
        start_step_index: int = 1,
    ) -> None:
        self.state.current_plan_artifact_id = plan_artifact_id
        self.state.current_plan_id = getattr(plan, "id", None)
        self.state.current_job_id = job_id
        self.bus.publish(
            "ai.worker.run.start",
            {
                "plan_id": getattr(plan, "id", None),
                "plan_artifact_id": plan_artifact_id,
                "job_id": self.state.current_job_id,
                "ts": time.time(),
            },
        )
        try:
            runner.run(
                plan,
                job_id=job_id,
                enqueue=False,
                start_step_index=start_step_index,
                plan_artifact_id=plan_artifact_id,
            )
        finally:
            self.bus.publish(
                "ai.worker.run.end",
                {
                    "plan_id": getattr(plan, "id", None),
                    "plan_artifact_id": plan_artifact_id,
                    "job_id": self.state.current_job_id,
                    "ts": time.time(),
                },
            )
            self.state.current_plan_artifact_id = None
            self.state.current_plan_id = None
            self.state.current_job_id = None


def _build_policy(cfg) -> Policy:
    policy_cfg = getattr(cfg, "policy", None)
    if not policy_cfg:
        return Policy()
    return Policy(
        allowed_tags=list(getattr(policy_cfg, "allowed_tags", []) or []),
        allowed_scopes=list(getattr(policy_cfg, "allowed_scopes", []) or []),
        allowed_tools=list(getattr(policy_cfg, "allowed_tools", []) or []),
        block_categories=list(getattr(policy_cfg, "block_categories", []) or []),
        autonomous_categories=list(getattr(policy_cfg, "autonomous_categories", []) or []),
    )


def _build_registry() -> ActionRegistry:
    pack_path = Path(__file__).resolve().parents[1] / "actions" / "packs" / "bjorn_core.yml"
    if pack_path.exists():
        return load_pack(str(pack_path))
    return ActionRegistry()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smolotchi AI worker")
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to config.toml (default: config.toml)",
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Run continuously and poll for queued jobs",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds between worker polls (default: 1.0)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Logging level (default: INFO)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    bus = SQLiteBus()
    store = ConfigStore(args.config)
    store.load()
    artifacts = ArtifactStore("/var/lib/smolotchi/artifacts")
    jobstore = JobStore(bus.db_path)
    registry = _build_registry()
    policy = _build_policy(store.get())
    action_runner = ActionRunner(bus=bus, artifacts=artifacts, policy=policy)
    worker = AIWorker(
        bus=bus,
        registry=registry,
        artifacts=artifacts,
        jobstore=jobstore,
        runner=action_runner,
        poll_interval_s=float(args.poll_interval),
    )

    if args.loop:
        worker._loop()
    else:
        worker.run_once()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
