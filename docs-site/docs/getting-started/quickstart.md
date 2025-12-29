# Quickstart

## Run the web UI

The Flask app is created in `smolotchi.api.web.create_app` and binds to configuration from `ConfigStore`.

Code: smolotchi/api/web.py:create_app, smolotchi/core/config.py:ConfigStore

Example invocation (repo layout):

```bash
python -m smolotchi.api.web
```

Code: smolotchi/api/web.py:create_app, smolotchi/__main__.py

## Run the worker

The AI worker loop is implemented by `AIWorker` and started by `smolotchi.ai.worker.main`.

Code: smolotchi/ai/worker.py:AIWorker, smolotchi/ai/worker.py:main

Example invocation:

```bash
python -m smolotchi.ai.worker
```

Code: smolotchi/ai/worker.py:main

## Run the CLI

The CLI entry point is `smolotchi.cli.main` and is invoked via `python -m smolotchi`.

Code: smolotchi/cli.py:main, smolotchi/__main__.py
