#!/usr/bin/env bash
set -euo pipefail

# One-shot bootstrap:
# - clones/updates repo + venv + editable install + env/config + dirs
# - installs wrapper + systemd units
# - enables + starts services
#
# Env overrides:
#   REPO_URL, BRANCH, USER_NAME
#   START_DISPLAY=1   # start display once (not enabled)

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[+] Smolotchi bootstrap starting"
echo "    REPO_URL=${REPO_URL:-https://github.com/161sam/smolotchi.git}"
echo "    BRANCH=${BRANCH:-main}"
echo "    USER_NAME=${USER_NAME:-smolotchi}"
echo "    START_DISPLAY=${START_DISPLAY:-0}"
echo

# 1) Install/update smolotchi repo + venv + env/config/dirs + wrapper
bash "$SCRIPT_DIR/install_smolotchi.sh"

USER_NAME="${USER_NAME:-smolotchi}"
SMOLO_REPO="/home/$USER_NAME/smolotchi"

if [[ ! -x "$SMOLO_REPO/scripts/pi_zero/install_systemd.sh" ]]; then
  echo "error: expected $SMOLO_REPO/scripts/pi_zero/install_systemd.sh"
  exit 1
fi

echo
echo "[+] Installing/Updating systemd units"
START_DISPLAY="${START_DISPLAY:-0}" bash "$SMOLO_REPO/scripts/pi_zero/install_systemd.sh"

echo
echo "[+] Quick status"
systemctl --no-pager --full status smolotchi-core smolotchi-web smolotchi-ai smolotchi-prune.timer || true
systemctl --no-pager --full status smolotchi-display || true

echo
echo "[+] Recent logs"
journalctl -u smolotchi-core -n 30 --no-pager || true
journalctl -u smolotchi-web  -n 30 --no-pager || true
journalctl -u smolotchi-ai   -n 30 --no-pager || true
journalctl -u smolotchi-display -n 30 --no-pager || true

echo
echo "[+] Done. Open Web UI (if running):"
echo "    http://<pi-ip>:<port>"
