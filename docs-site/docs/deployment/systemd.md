# systemd Deployment

Systemd unit files are stored in `packaging/systemd/` and are installed by the CLI's `install-systemd` command.

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-web.service, smolotchi/cli.py:cmd_install_systemd

## Runtime and state paths

`/run/smolotchi` and `/run/smolotchi/locks` are created via `systemd-tmpfiles` so the CLI can run
without sudo even before services start. Services still use `RuntimeDirectory=smolotchi` and
`StateDirectory=smolotchi` as a safety net for runtime/state ownership and permissions.

Troubleshooting:

```bash
systemd-tmpfiles --cat-config | grep smolotchi
systemd-tmpfiles --create --prefix=/run/smolotchi
ls -ld /run/smolotchi /run/smolotchi/locks
```

## Units

- `smolotchi-core.service` – core state machine daemon
- `smolotchi-ai.service` – AI worker
- `smolotchi-web.service` – Flask web UI
- `smolotchi-display.service` – display daemon
- `smolotchi-prune.service` / `smolotchi-prune.timer` – retention pruning

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-ai.service, packaging/systemd/smolotchi-web.service, packaging/systemd/smolotchi-display.service, packaging/systemd/smolotchi-prune.service, packaging/systemd/smolotchi-prune.timer
