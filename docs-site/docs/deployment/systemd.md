# systemd Deployment

Systemd unit files are stored in `packaging/systemd/` and are installed by the canonical
`scripts/deploy.sh` flow. The deploy script installs units and drop-ins, then writes a
`05-venv-execstart.conf` override so each service runs
`/opt/smolotchi/current/.venv/bin/python -m smolotchi.cli <cmd>` (no `/home` drift).
The default layout targets `/opt/smolotchi/current` for code, `/var/lib/smolotchi` for
state, and `/run/smolotchi` for runtime paths so units stay compatible with
`ProtectHome=true` and `ProtectSystem=strict`.

Code: scripts/deploy.sh, packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-web.service

## Python extras

Install the optional dependency groups that match your deployment (the deploy script already installs
`requirements/base.txt` and `requirements/pi_zero.txt`):

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
- `smolotchi-core-net.service` – opt-in core with `CAP_NET_ADMIN`
- `smolotchi-ai.service` – AI worker
- `smolotchi-web.service` – web UI (Gunicorn when available, Flask dev server fallback)
- `smolotchi-display.service` – display daemon
- `smolotchi-prune.service` / `smolotchi-prune.timer` – retention pruning

Code: packaging/systemd/smolotchi-core.service, packaging/systemd/smolotchi-ai.service, packaging/systemd/smolotchi-web.service, packaging/systemd/smolotchi-display.service, packaging/systemd/smolotchi-prune.service, packaging/systemd/smolotchi-prune.timer

## Web bind and port

By default the web unit binds to `127.0.0.1:8080`. Override it in `/etc/smolotchi/env` if you need
LAN access.

Security note: only bind to `0.0.0.0` when you explicitly want the UI reachable on the LAN.
Otherwise keep the loopback default or put the service behind a reverse proxy/firewall.

## Prod-like layout (default)

The deploy script syncs the project into `/opt/smolotchi/current` and writes units that use:

- `WorkingDirectory=/var/lib/smolotchi`
- `PYTHONPATH=/opt/smolotchi/current`
- `ReadWritePaths=/var/lib/smolotchi /run/smolotchi`
- `ReadOnlyPaths=/opt/smolotchi/current`

If you prefer to manage the code manually, clone or rsync the repo to `/opt/smolotchi/current`
before running the deploy script.

### Upgrade / rollback workflow

1. Sync new code into `/opt/smolotchi/current` (or update the repo there).
2. Recreate the venv under `/opt/smolotchi/current/.venv` for the new version.
3. Run `sudo ./scripts/deploy.sh --apply` (or re-run the curl | bash install).
4. Restart services (`sudo systemctl restart smolotchi-core smolotchi-web smolotchi-display smolotchi-ai`).

Rollback:

1. Restore the previous code under `/opt/smolotchi/current` (or point it back to the prior release).
2. Re-run `sudo ./scripts/deploy.sh --apply` (or re-run the curl | bash install).
3. Restart the services to pick up the rollback.

## Troubleshooting Gunicorn

If the web unit falls back to Flask or fails because `gunicorn` is missing, reinstall the web extras and re-run
the deploy script:

```bash
pip install -e '.[web,core]'
sudo ./scripts/deploy.sh --apply
```
