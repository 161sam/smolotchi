# Glossary

- **Artifact**: A JSON/text/file payload stored by `ArtifactStore` and indexed in `index.json`.
  - Code: smolotchi/core/artifacts.py:ArtifactStore
- **Stage request**: An approval request artifact emitted when a plan step requires confirmation.
  - Code: smolotchi/actions/plan_runner.py:PlanRunner._ensure_stage_request, smolotchi/core/artifacts.py:ArtifactStore.find_latest_stage_request
- **Plan**: A list of steps created by the planner and executed by the plan runner.
  - Code: smolotchi/actions/planners/ai_planner.py:ActionPlan, smolotchi/actions/plan_runner.py:PlanRunner.run
