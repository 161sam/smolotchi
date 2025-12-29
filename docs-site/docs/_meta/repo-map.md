# Repository Map

## Top-level layout

- `smolotchi/` – Python package (CLI, AI worker, web UI, actions, core)
- `scripts/` – helper scripts
- `packaging/` – systemd units
- `requirements/` – dependency sets
- `config.toml` – default runtime config file

Code: smolotchi/__init__.py, packaging/systemd/smolotchi-core.service, requirements/base.txt, config.toml

## Key Python packages

- `smolotchi/actions` – action registry, runners, plan runners, and packs
- `smolotchi/ai` – worker loop + planner replay
- `smolotchi/api` – Flask web UI
- `smolotchi/core` – config, policy, artifacts, paths, bus, watchdog

Code: smolotchi/actions/registry.py:ActionRegistry, smolotchi/ai/worker.py:AIWorker, smolotchi/api/web.py:create_app, smolotchi/core/config.py:ConfigStore

## Entry points

- `python -m smolotchi` → CLI
- `python -m smolotchi.api.web` → web UI
- `python -m smolotchi.ai.worker` → worker

Code: smolotchi/__main__.py, smolotchi/cli.py:main, smolotchi/api/web.py:create_app, smolotchi/ai/worker.py:main
