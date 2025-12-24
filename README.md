# Smolotchi

Smolotchi is a clean-room lab orchestration scaffold inspired by Pwnagotchi and Bjorn.
This repository provides a minimal v0.0.1 skeleton with a state machine, SQLite event bus,
Flask/Jinja web UI, and a Waveshare 2.13 v4 display daemon.

## Layout

```text
smolotchi/
  smolotchi/
    core/       # state machine, policy, event bus
    api/        # Flask/Jinja web UI
    display/    # e-paper display daemon
  packaging/
    systemd/
  scripts/
```

## Quickstart (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
python -m smolotchi.api.web
```

Visit http://localhost:8080
