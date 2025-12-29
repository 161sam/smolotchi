# Smolotchi Pi Zero Bootstrap

This directory contains a complete bootstrap flow for a fresh Raspberry Pi OS Lite image.

---

## Pi Zero Setup (Raspberry Pi OS Lite)

Bootstrap a fresh Raspberry Pi OS Lite installation with the provided script.

**Option A: curl | bash (example)**

```bash
curl -sfL https://raw.githubusercontent.com/161sam/smolotchi/main/scripts/pi_zero/bootstrap.sh | \
  sudo bash -s -- --repo "https://github.com/161sam/smolotchi.git" --branch main --enable-sudo
```

**Option B: clone the repo and run locally**

```bash
git clone https://github.com/161sam/smolotchi.git
cd smolotchi
sudo ./scripts/pi_zero/bootstrap.sh --repo "https://github.com/161sam/smolotchi.git" --branch main --enable-sudo
```

Services are installed to `/etc/systemd/system` and enabled on boot. Check status:

```bash
sudo systemctl status smolotchi-core smolotchi-web smolotchi-ai-worker --no-pager
sudo journalctl -u smolotchi-core -n 50 --no-pager
```

Start/stop/restart:

```bash
sudo systemctl start smolotchi-core smolotchi-web smolotchi-ai-worker
sudo systemctl stop smolotchi-core smolotchi-web smolotchi-ai-worker
sudo systemctl restart smolotchi-core smolotchi-web smolotchi-ai-worker
```

See `scripts/pi_zero/README.md` for a smoke checklist.

---

## Quick start

```bash
sudo ./scripts/pi_zero/bootstrap_pi_zero.sh
```

Then, as the `smolotchi` user:

```bash
./scripts/pi_zero/install_smolotchi.sh
```

Finally, as root:

```bash
sudo ./scripts/pi_zero/install_systemd.sh
```

Optional legacy flags (bootstrap.sh):

* `--user smolotchi`
* `--with-display`
* `--enable-sudo`

The bootstrap script installs dependencies, creates the `smolotchi` user, configures
`/etc/smolotchi`, provisions a venv at `/home/smolotchi/.venv`, and enables systemd services.

---

## Smoke checklist

```bash
systemctl status smolotchi-core smolotchi-web smolotchi-ai --no-pager
journalctl -u smolotchi-core -n 50 --no-pager
curl -sf http://127.0.0.1:8080/health || true
python -m smolotchi.cli health
python -m smolotchi.cli events --limit 20
```
