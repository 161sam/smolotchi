# systemd Deployment

Systemd unit files are stored in `packaging/systemd/` and are installed by the CLI's `install-systemd` command.
The installer uses the project's `.venv/bin/python` when available, otherwise it falls back to the currently running
interpreter (or `/usr/bin/python3` if needed). The default `prod` layout targets `/opt/smolotchi/current` for code,
`/var/lib/smolotchi` for state, and `/run/smolotchi` for runtime paths so units stay compatible with
`ProtectHome=true` and `ProtectSystem=strict`.

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-web.service, smolotchi/cli.py:cmd_install_systemd

## Python extras

Install the optional dependency groups that match your deployment:

```bash
pip install -e '.[web,core]'
```

`web` installs Flask + Gunicorn, `core` installs Jinja2 + PyYAML, and `display` adds Pillow if you enable the
display daemon.

## Runtime and state paths

`/run/smolotchi` and `/run/smolotchi/locks` are created via `systemd-tmpfiles` so the CLI can run
without sudo even before services start. Services still use `RuntimeDirectory=smolotchi` and
`StateDirectory=smolotchi` as a safety net for runtime/state ownership and permissions. Units also
set `ReadWritePaths=/var/lib/smolotchi /run/smolotchi` (and `ReadOnlyPaths=/opt/smolotchi/current`
in prod layout) so they run cleanly under strict systemd hardening.

Troubleshooting:

```bash
systemd-tmpfiles --cat-config | grep smolotchi
systemd-tmpfiles --create /etc/tmpfiles.d/smolotchi.conf
systemd-tmpfiles --create --prefix=/run/smolotchi
ls -ld /run/smolotchi /run/smolotchi/locks
```

## Units

- `smolotchi-core.service` – core state machine daemon
- `smolotchi-ai-worker.service` – AI worker
- `smolotchi-web.service` – web UI (Gunicorn when available, Flask dev server fallback)
- `smolotchi-display.service` – display daemon
- `smolotchi-prune.service` / `smolotchi-prune.timer` – retention pruning

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-ai-worker.service, packaging/systemd/smolotchi-web.service, packaging/systemd/smolotchi-display.service, packaging/systemd/smolotchi-prune.service, packaging/systemd/smolotchi-prune.timer

## Prod-like layout (default)

The installer syncs the project into `/opt/smolotchi/current` and writes units that use:

- `WorkingDirectory=/var/lib/smolotchi`
- `PYTHONPATH=/opt/smolotchi/current`
- `ReadWritePaths=/var/lib/smolotchi /run/smolotchi`
- `ReadOnlyPaths=/opt/smolotchi/current`

If you prefer to manage the code manually, clone or rsync the repo to `/opt/smolotchi/current`
before running the installer, or use `--layout project` to keep the units pointing at your project
directory (still using `/var/lib/smolotchi` as the working directory).

### Upgrade / rollback workflow

1. Sync new code into `/opt/smolotchi/current` (or update the repo there).
2. If you ship a venv, recreate it under `/opt/smolotchi/current/.venv` for the new version.
3. Run `sudo smolotchi install-systemd --project-dir /opt/smolotchi/current --layout prod --web-server auto`.
4. Restart services (`sudo systemctl restart smolotchi-core smolotchi-web smolotchi-display smolotchi-ai-worker`).

Rollback:

1. Restore the previous code under `/opt/smolotchi/current` (or point it back to the prior release).
2. Re-run `sudo smolotchi install-systemd --project-dir /opt/smolotchi/current --layout prod --web-server auto`.
3. Restart the services to pick up the rollback.

## Troubleshooting Gunicorn

If the web unit falls back to Flask or fails because `gunicorn` is missing, reinstall the web extras and re-run
the installer:

```bash
pip install -e '.[web,core]'
sudo smolotchi install-systemd --project-dir /opt/smolotchi/current --layout prod --web-server auto
```
