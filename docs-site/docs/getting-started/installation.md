# Installation

## Python dependencies

The repository provides pip requirement sets for general usage and Raspberry Pi Zero usage.

- `requirements/base.txt`
- `requirements/pi_zero.txt`

Code: requirements/base.txt, requirements/pi_zero.txt

## Config file location

Runtime config is loaded from `config.toml` by default. Both the CLI and web app accept a `--config`/`config_path` argument to override this path.

Code: smolotchi/core/paths.py:resolve_config_path, smolotchi/core/config.py:ConfigStore, smolotchi/ai/worker.py:main, smolotchi/api/web.py:create_app

## Pi Zero / systemd installation (recommended)

For systemd on-device installs, **avoid editable installs** (`pip install -e .`). Editable installs reference repo paths under `/home/...`, which can be blocked by systemd hardening (e.g. `ProtectHome`), causing `ModuleNotFoundError` or `PermissionError`.

### Option A: system-wide non-editable install

```bash
sudo python3 -m pip uninstall -y smolotchi --break-system-packages || true
sudo python3 -m pip install . --break-system-packages
```

### Option B: dedicated venv under /var/lib/smolotchi/venv

```bash
sudo python3 -m venv /var/lib/smolotchi/venv
sudo /var/lib/smolotchi/venv/bin/python -m pip install --upgrade pip
sudo /var/lib/smolotchi/venv/bin/python -m pip install .
```

If you use a venv, point systemd to it via `/etc/smolotchi/env`:

```bash
SMOLOTCHI_PY=/var/lib/smolotchi/venv/bin/python
```

### Troubleshooting

- `ModuleNotFoundError: No module named 'smolotchi'` usually means systemd is using a different Python context than your install.
- `PermissionError` pointing at `__editable__..._finder.py` means the service is running an editable install and is blocked from reading repo paths under `/home`.

Fix: remove the editable install and install non-editable (Option A or B above).
