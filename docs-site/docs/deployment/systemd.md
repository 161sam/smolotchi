# systemd Deployment

Systemd unit files are stored in `packaging/systemd/` and are installed by the CLI's `install-systemd` command.

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-web.service, smolotchi/cli.py:cmd_install_systemd

## Runtime and state paths

All services create `/run/smolotchi` via `RuntimeDirectory=smolotchi` and `/var/lib/smolotchi` via
`StateDirectory=smolotchi`. These are the only writable runtime/state paths when hardening is enabled.

## Units

- `smolotchi-core.service` – core state machine daemon
- `smolotchi-ai.service` – AI worker
- `smolotchi-web.service` – Flask web UI
- `smolotchi-display.service` – display daemon
- `smolotchi-prune.service` / `smolotchi-prune.timer` – retention pruning

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-ai.service, packaging/systemd/smolotchi-web.service, packaging/systemd/smolotchi-display.service, packaging/systemd/smolotchi-prune.service, packaging/systemd/smolotchi-prune.timer
