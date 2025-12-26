import tempfile
import unittest

from smolotchi.actions.registry import ActionRegistry
from smolotchi.actions.runner import ActionRunner
from smolotchi.actions.schema import ActionSpec
from smolotchi.ai.worker import AIWorker
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.policy import Policy


class WorkerResumeTest(unittest.TestCase):
    def test_stage_resume_executes_blocked_step_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = SQLiteBus(f"{tmpdir}/events.db")
            artifacts = ArtifactStore(f"{tmpdir}/artifacts")
            jobs = JobStore(f"{tmpdir}/events.db")
            registry = ActionRegistry()
            registry.register(
                ActionSpec(
                    id="test.action",
                    name="Test Action",
                    category="test",
                    risk="safe",
                )
            )
            executed_steps: list[int] = []

            def _run_action(*, step_index: int, **_):
                executed_steps.append(step_index)
                return {"ok": True, "summary": "ok"}

            registry.register_impl("test.action", _run_action)
            runner = ActionRunner(
                bus=bus,
                artifacts=artifacts,
                policy=Policy(),
                registry=registry,
            )
            worker = AIWorker(
                bus=bus,
                registry=registry,
                artifacts=artifacts,
                jobstore=jobs,
                runner=runner,
            )

            plan_doc = {
                "id": "plan-test",
                "mode": "manual",
                "scope": "10.0.0.0/24",
                "note": "resume-test",
                "steps": [
                    {"action_id": "test.action", "payload": {"step": 1}},
                    {"action_id": "test.action", "payload": {"step": 2}},
                ],
            }
            plan_meta = artifacts.put_json(
                kind="ai_plan",
                title="AI Plan Test",
                payload=plan_doc,
            )
            req_meta = artifacts.put_json(
                kind="ai_run_request",
                title="AI Run Request",
                payload={"plan_artifact_id": plan_meta.id},
            )

            jobs.enqueue(
                {
                    "id": "job-test",
                    "kind": "ai_plan",
                    "scope": "10.0.0.0/24",
                    "note": f"req:{req_meta.id} resume_from:2",
                }
            )

            worker.run_once()

            self.assertEqual(executed_steps, [2])
            job = jobs.get("job-test")
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "done")


if __name__ == "__main__":
    unittest.main()
