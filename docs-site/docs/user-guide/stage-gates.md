# Stage Gates (Policy Approvals)

## Where approvals are enforced

Stage gating is enforced by the plan runner and worker when a step raises a `StageRequired` error. The plan runner emits a stage request artifact and marks the job as blocked.

Code: smolotchi/actions/plan_runner.py:PlanRunner._ensure_stage_request, smolotchi/actions/plan_runner.py:PlanRunner._emit_blocked, smolotchi/ai/errors.py:StageRequired

## Approval storage

Stage requests and approvals are stored in the artifact store. Pending status is derived by checking for matching approvals.

Code: smolotchi/core/artifacts.py:ArtifactStore.is_stage_request_pending, smolotchi/core/artifacts.py:ArtifactStore.find_latest_stage_approval_for_request

## UI routes

Approvals are created via the AI stage approval route.

Code: smolotchi/api/web.py:ai_stage_approve
