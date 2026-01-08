#!/usr/bin/env bash
set -euo pipefail

# One-shot bootstrap:
# - clones/updates repo + venv + editable install + env/config + dirs
# - installs wrapper + systemd units
# - enables + starts services
#
# Env overrides (optional):
#   REPO_URL, BRANCH, USER_NAME

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[+] Smolotchi bootstrap starting"
echo "    REPO_URL=${REPO_URL:-https://github.com/161sam/smolotchi.git}"
echo "    BRANCH=${BRANCH:-main}"
echo "    USER_NAME=${USER_NAME:-smolotchi}"
echo

# 1) Install/update smolotchi repo + venv + env/config/dirs + wrapper
"$SCRIPT_DIR/install_smolotchi.sh"

# 2) Now we can run install_systemd from the cloned repo path (reliable)
USER_NAME="${USER_NAME:-smolotchi}"
SMOLO_REPO="/home/$USER_NAME/smolotchi"

if [[ ! -x "$SMOLO_REPO/scripts/pi_zero/install_systemd.sh" ]]; then
  echo "error: expected $SMOLO_REPO/scripts/pi_zero/install_systemd.sh"
  exit 1
fi

echo
echo "[+] Installing/Updating systemd units"
bash "$SMOLO_REPO/scripts/pi_zero/install_systemd.sh"

echo
echo "[+] Quick status"
systemctl --no-pager --full status smolotchi-core smolotchi-web smolotchi-ai smolotchi-prune.timer || true
systemctl --no-pager --full status smolotchi-display || true

echo
echo "[+] Quick health"
sudo -u "$USER_NAME" /usr/local/bin/smolotchi status || true
sudo -u "$USER_NAME" /usr/local/bin/smolotchi health || true

echo
echo "[+] Done."
echo "Logs:"
echo "  journalctl -u smolotchi-core -n 80 --no-pager"
echo "  journalctl -u smolotchi-web  -n 80 --no-pager"
echo "  journalctl -u smolotchi-ai   -n 80 --no-pager"
