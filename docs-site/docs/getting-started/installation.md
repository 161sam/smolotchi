# Installation

## Python dependencies

The repository provides pip requirement sets for general usage and Raspberry Pi Zero usage.

- `requirements/base.txt`
- `requirements/pi_zero.txt`

Code: requirements/base.txt, requirements/pi_zero.txt

## Config file location

Runtime config is loaded from `config.toml` by default. For systemd installs, the deploy script enforces
`/etc/smolotchi/config.toml` and writes `SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml` to `/etc/smolotchi/env`.

Code: smolotchi/core/paths.py:resolve_config_path, smolotchi/core/config.py:ConfigStore, smolotchi/ai/worker.py:main, smolotchi/api/web.py:create_app

## Pi Zero / systemd installation (recommended)

Use the canonical deploy script (pins `/opt/smolotchi/current` and `/opt/smolotchi/current/.venv`):

```bash
curl -sfL https://raw.githubusercontent.com/<owner>/<repo>/main/scripts/deploy.sh | \
  sudo bash -s -- --repo "https://github.com/<owner>/<repo>.git" --branch main --apply
```

Local repo usage:

```bash
sudo ./scripts/deploy.sh --apply
```

### Drift checks

```bash
/opt/smolotchi/current/.venv/bin/python -c "import smolotchi, smolotchi.cli as c; print('smolotchi:', smolotchi.__file__); print('cli:', c.__file__)"
/opt/smolotchi/current/.venv/bin/pip show -f smolotchi
```
