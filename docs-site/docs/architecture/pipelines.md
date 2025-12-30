# Pipelines & Execution Flow

## Job → Plan → Action flow

The worker loop (`AIWorker`) reads jobs, builds or loads plans, and executes steps with the plan runner and action runner.

Code: smolotchi/ai/worker.py:AIWorker._tick, smolotchi/ai/worker.py:AIWorker._process_job, smolotchi/actions/plan_runner.py:PlanRunner.run, smolotchi/actions/runner.py:ActionRunner.execute

```
AIWorker -> AIPlanner: generate(plan inputs)
AIPlanner -> AIWorker: ActionPlan
AIWorker -> PlanRunner: run(plan)
PlanRunner -> ActionRunner: execute(step action)
ActionRunner -> PlanRunner: ActionResult
PlanRunner -> AIWorker: plan result
```

Code: smolotchi/ai/worker.py:AIWorker._run_plan_object, smolotchi/actions/planners/ai_planner.py:AIPlanner.generate, smolotchi/actions/plan_runner.py:PlanRunner.run, smolotchi/actions/runner.py:ActionRunner.execute

## Stage gates

Risk-based approvals are enforced by the plan runner and the worker. When a step is blocked, the run emits stage request artifacts and requires approval artifacts before resuming.

Code: smolotchi/actions/plan_runner.py:PlanRunner._risk_allowed, smolotchi/actions/plan_runner.py:PlanRunner._ensure_stage_request, smolotchi/ai/worker.py:AIWorker._approved_stage_request_ids

## Artifacts

Artifacts are persisted by the `ArtifactStore` and referenced by job and plan run metadata.

Code: smolotchi/core/artifacts.py:ArtifactStore.put_json, smolotchi/actions/planners/ai_planner.py:AIPlanner.generate
