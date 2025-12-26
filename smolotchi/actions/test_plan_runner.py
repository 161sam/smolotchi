import tempfile
import unittest

from smolotchi.actions.plan_runner import PlanRunner
from smolotchi.actions.registry import ActionRegistry
from smolotchi.actions.runner import ActionRunner
from smolotchi.actions.schema import ActionSpec
from smolotchi.core.artifacts import ArtifactStore
from smolotchi.core.bus import SQLiteBus
from smolotchi.core.jobs import JobStore
from smolotchi.core.policy import Policy


class PlanRunnerPolicyGateTest(unittest.TestCase):
    def test_policy_block_creates_stage_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bus = SQLiteBus(f"{tmpdir}/events.db")
            artifacts = ArtifactStore(f"{tmpdir}/artifacts")
            jobs = JobStore(f"{tmpdir}/events.db")
            registry = ActionRegistry()
            registry.register(
                ActionSpec(
                    id="net.port_scan",
                    name="Port Scan",
                    category="network_scan",
                    risk="caution",
                )
            )

            class _Step:
                action_id = "net.port_scan"
                payload = {"target": "10.0.0.1"}
                why = ["test"]
                score = 0.1

            class _Plan:
                id = "plan-test"
                scope = "10.0.0.0/24"
                note = "policy-block-test"
                steps = [_Step()]

            runner = PlanRunner(
                bus=bus,
                registry=registry,
                jobstore=jobs,
                artifacts=artifacts,
                runner=ActionRunner(
                    bus=bus,
                    artifacts=artifacts,
                    policy=Policy(),
                    registry=registry,
                ),
            )
            runner.run(_Plan(), job_id="job-test", enqueue=True)

            stage_requests = artifacts.list(limit=10, kind="ai_stage_request")
            self.assertTrue(stage_requests, "expected ai_stage_request artifact")
            req_doc = artifacts.get_json(stage_requests[0].id) or {}
            self.assertEqual(req_doc.get("job_id"), "job-test")
            job = jobs.get("job-test")
            self.assertIsNotNone(job)
            self.assertEqual(job.status, "blocked")


if __name__ == "__main__":
    unittest.main()
