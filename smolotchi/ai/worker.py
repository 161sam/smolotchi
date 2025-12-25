from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Optional

from smolotchi.actions.plan_runner import PlanRunner
from smolotchi.actions.planners.ai_planner import AIPlanner
from smolotchi.actions.registry import ActionRegistry
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore


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
        poll_interval_s: float = 1.0,
    ) -> None:
        self.bus = bus
        self.registry = registry
        self.artifacts = artifacts
        self.jobstore = jobstore
        self.poll_interval_s = poll_interval_s

        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.state = WorkerState()
        self.watchdog_s = float(os.environ.get("SMO_AI_WATCHDOG_S", "300"))
        self._last_progress_by_job: dict[str, float] = {}

    def _extract_req_id(self, note: str) -> Optional[str]:
        note = note or ""
        for part in note.split():
            if part.startswith("req:"):
                return part.split("req:", 1)[1].strip()
        return None

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

        while not self._stop.is_set():
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

                queued = self.jobstore.list(limit=20, status="queued")
                queued = [
                    j for j in queued if getattr(j, "kind", "") == "ai_plan"
                ]
                queued = sorted(queued, key=lambda j: j.created_ts)

                for job in queued:
                    if getattr(job, "status", "") == "cancelled":
                        continue

                    job_id = job.id
                    req_id = self._extract_req_id(
                        getattr(job, "note", "") or ""
                    )
                    if not req_id:
                        self.jobstore.mark_failed(
                            job_id,
                            note="missing req:<artifact_id> in job.note",
                        )
                        self.bus.publish(
                            "ai.worker.job_failed",
                            {"job_id": job_id, "error": "missing run request"},
                        )
                        continue

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
                        continue

                    plan_artifact_id = (
                        req.get("plan_artifact_id") or ""
                    ).strip()
                    scope = (req.get("scope") or "").strip()
                    note = req.get("note") or ""

                    try:
                        self.jobstore.mark_running(job_id)
                    except Exception:
                        pass

                    self.bus.publish(
                        "ai.worker.dequeue",
                        {"job_id": job_id, "req_id": req_id, "ts": time.time()},
                    )

                    if plan_artifact_id:
                        self._run_plan_artifact(plan_artifact_id, job_id=job_id)
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
                        )
                        self._run_plan_object(plan, runner, job_id=job_id)

                    break

            except Exception as exc:
                self.state.last_error = str(exc)
                self.bus.publish("ai.worker.error", {"error": str(exc), "ts": time.time()})

            time.sleep(self.poll_interval_s)

        self.state.running = False
        self.bus.publish("ai.worker.stopped", {"ts": time.time()})

    def _run_plan_artifact(self, plan_artifact_id: str, *, job_id: str) -> None:
        plan_doc = self.artifacts.get_json(plan_artifact_id)
        if not plan_doc:
            self.bus.publish("ai.worker.plan_missing", {"artifact_id": plan_artifact_id})
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
        )

        self._run_plan_object(
            plan,
            runner,
            plan_artifact_id=plan_artifact_id,
            job_id=job_id,
        )

    def _run_plan_object(
        self,
        plan,
        runner: PlanRunner,
        *,
        plan_artifact_id: Optional[str] = None,
        job_id: str,
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
            runner.run(plan, job_id=job_id, enqueue=False)
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
