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

## systemd quickstart (Pi Zero)

Install systemd units and use a non-editable install for systemd:

```bash
sudo ./scripts/pi_zero/install_systemd.sh
sudo python3 -m pip install . --break-system-packages
sudo systemctl restart smolotchi-core smolotchi-web smolotchi-ai
```

Check status and logs:

```bash
sudo systemctl status smolotchi-core smolotchi-web smolotchi-ai --no-pager
sudo journalctl -u smolotchi-core -n 100 --no-pager
```

See the installation guide for the full non-editable / venv recommendations.
