#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

echo "[+] Installing systemd units"

cd "$(dirname "$0")/../.."
PROJECT_DIR="$(pwd)"

install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-core.service"   /etc/systemd/system/smolotchi-core.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-ai.service"     /etc/systemd/system/smolotchi-ai.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-web.service"    /etc/systemd/system/smolotchi-web.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-display.service" /etc/systemd/system/smolotchi-display.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.service"  /etc/systemd/system/smolotchi-prune.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.timer"    /etc/systemd/system/smolotchi-prune.timer

systemctl daemon-reload

systemctl enable smolotchi-core smolotchi-ai smolotchi-web smolotchi-prune.timer
systemctl restart smolotchi-core smolotchi-ai || true
systemctl restart smolotchi-web || true
systemctl start smolotchi-prune.timer

echo "[+] systemd services started"
echo "Check:"
echo "  systemctl status smolotchi-core smolotchi-web smolotchi-ai --no-pager"
