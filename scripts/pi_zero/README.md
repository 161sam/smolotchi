# Smolotchi Pi Zero Bootstrap

This directory contains a complete bootstrap flow for a fresh Raspberry Pi OS Lite image.

## Quick start

```bash
sudo ./scripts/pi_zero/bootstrap.sh \
  --repo "https://github.com/<you>/smolotchi.git" \
  --branch main \
  --enable-sudo
```

Optional flags:

* `--user smolotchi`
* `--with-display`
* `--enable-sudo`

The bootstrap script installs dependencies, creates the `smolotchi` user, configures
`/etc/smolotchi`, provisions a venv at `/opt/smolotchi/.venv`, and enables systemd services.

## Smoke checklist

```bash
systemctl status smolotchi-core smolotchi-web smolotchi-ai-worker --no-pager
journalctl -u smolotchi-core -n 50 --no-pager
curl -sf http://127.0.0.1:8080/health || true
python -m smolotchi.cli health
python -m smolotchi.cli events --limit 20
```
