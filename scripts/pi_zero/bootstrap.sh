#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[+] Smolotchi bootstrap starting"
echo "    REPO_URL=${REPO_URL:-https://github.com/161sam/smolotchi.git}"
echo "    BRANCH=${BRANCH:-main}"
echo "    USER_NAME=${USER_NAME:-smolotchi}"
echo "    INSTALL_WAVESHARE=${INSTALL_WAVESHARE:-1}"
echo "    ENABLE_DISPLAY=${ENABLE_DISPLAY:-0}"
echo "    START_DISPLAY=${START_DISPLAY:-0}"
echo

bash "$SCRIPT_DIR/install_smolotchi.sh"

USER_NAME="${USER_NAME:-smolotchi}"
SMOLO_REPO="/home/$USER_NAME/smolotchi"

echo
echo "[+] Installing/Updating systemd units"
ENABLE_DISPLAY="${ENABLE_DISPLAY:-0}" START_DISPLAY="${START_DISPLAY:-0}" \
  bash "$SMOLO_REPO/scripts/pi_zero/install_systemd.sh"

echo
echo "[+] Quick status"
systemctl --no-pager --full status smolotchi-core smolotchi-web smolotchi-ai smolotchi-prune.timer || true
systemctl --no-pager --full status smolotchi-display || true

echo
echo "[+] Done."
