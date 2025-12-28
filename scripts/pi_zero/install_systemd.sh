#!/usr/bin/env bash
set -euo pipefail

echo "[+] Installing systemd units"

cp packaging/systemd/*.service /etc/systemd/system/
cp packaging/systemd/*.timer /etc/systemd/system/ || true

systemctl daemon-reexec
systemctl daemon-reload

systemctl enable \
  smolotchi-core \
  smolotchi-ai \
  smolotchi-web \
  smolotchi-prune.timer

systemctl start smolotchi-core
systemctl start smolotchi-ai
systemctl start smolotchi-web
systemctl start smolotchi-prune.timer

echo "[+] systemd services started"
