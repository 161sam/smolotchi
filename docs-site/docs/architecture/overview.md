# Architecture Overview

## Core components

- **Config + policy**: Config is loaded via `ConfigStore`, policy checks live in `smolotchi/core/policy.py`.
- **Artifacts**: Stored and indexed by `ArtifactStore` under the artifact root.
- **Actions + planning**: Action specs are loaded into `ActionRegistry` and executed by `ActionRunner` / `PlanRunner`.
- **Worker loop**: `AIWorker` polls jobs and runs plans.
- **Web UI**: Flask app in `smolotchi/api/web.py`.

Code: smolotchi/core/config.py:ConfigStore, smolotchi/core/policy.py:Policy, smolotchi/core/artifacts.py:ArtifactStore, smolotchi/actions/registry.py:ActionRegistry, smolotchi/actions/runner.py:ActionRunner, smolotchi/actions/plan_runner.py:PlanRunner, smolotchi/ai/worker.py:AIWorker, smolotchi/api/web.py:create_app

## Entry points

- `python -m smolotchi` → CLI
- `python -m smolotchi.api.web` → web UI
- `python -m smolotchi.ai.worker` → worker

Code: smolotchi/__main__.py, smolotchi/cli.py:main, smolotchi/api/web.py:create_app, smolotchi/ai/worker.py:main
