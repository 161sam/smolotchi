#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

cd "$(dirname "$0")/../.."
PROJECT_DIR="$(pwd)"

echo "[+] Installing smolotchi wrapper + systemd units from: $PROJECT_DIR"

install -m 0755 "$PROJECT_DIR/packaging/bin/smolotchi" /usr/local/bin/smolotchi

install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-core.service"    /etc/systemd/system/smolotchi-core.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-ai.service"      /etc/systemd/system/smolotchi-ai.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-web.service"     /etc/systemd/system/smolotchi-web.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-display.service" /etc/systemd/system/smolotchi-display.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.service"   /etc/systemd/system/smolotchi-prune.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.timer"     /etc/systemd/system/smolotchi-prune.timer

systemctl daemon-reload

# Enable + start default services (autostart after reboot)
systemctl enable --now smolotchi-core smolotchi-ai smolotchi-web smolotchi-prune.timer

# display: opt-in
if [[ "${ENABLE_DISPLAY:-0}" == "1" ]]; then
  systemctl enable smolotchi-display.service
  echo "[+] display enabled (autostart)"
else
  echo "[i] display not enabled (set ENABLE_DISPLAY=1 to enable autostart)"
fi

if [[ "${START_DISPLAY:-0}" == "1" ]]; then
  systemctl start smolotchi-display.service || true
  echo "[+] display started (one-shot)"
else
  echo "[i] display not started (set START_DISPLAY=1 to start once)"
fi

echo "[+] Done"
