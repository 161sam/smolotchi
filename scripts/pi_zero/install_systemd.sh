#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

cd "$(dirname "$0")/../.."
PROJECT_DIR="$(pwd)"

echo "[+] Installing smolotchi wrapper + systemd units from: $PROJECT_DIR"

# 1) wrapper must exist (units call /usr/local/bin/smolotchi)
install -m 0755 "$PROJECT_DIR/packaging/bin/smolotchi" /usr/local/bin/smolotchi

# 2) units/timers
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-core.service"    /etc/systemd/system/smolotchi-core.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-ai.service"      /etc/systemd/system/smolotchi-ai.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-web.service"     /etc/systemd/system/smolotchi-web.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-display.service" /etc/systemd/system/smolotchi-display.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.service"   /etc/systemd/system/smolotchi-prune.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.timer"     /etc/systemd/system/smolotchi-prune.timer

systemctl daemon-reload

# enable + start (start even if already enabled)
systemctl enable --now smolotchi-core smolotchi-ai smolotchi-web smolotchi-prune.timer
# optional display: enable only if you actually use it
systemctl enable --now smolotchi-display || true

echo "[+] systemd services started"
echo "Check:"
echo "  systemctl status smolotchi-core smolotchi-web smolotchi-ai smolotchi-display --no-pager"
