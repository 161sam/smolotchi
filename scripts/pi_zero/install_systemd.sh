#!/usr/bin/env bash
set -euo pipefail

echo "[+] Installing systemd units"

cp packaging/systemd/*.service /etc/systemd/system/
cp packaging/systemd/*.timer /etc/systemd/system/ || true
install -m 0755 packaging/bin/smolotchi /usr/local/bin/smolotchi

systemctl daemon-reexec
systemctl daemon-reload

systemctl enable --now \
  smolotchi-core \
  smolotchi-ai \
  smolotchi-web \
  smolotchi-prune.timer
if [[ "${ENABLE_CORE_NET_ADMIN:-0}" == "1" ]]; then
  systemctl disable --now smolotchi-core || true
  systemctl enable --now smolotchi-core-net
  echo "[+] core-net enabled (CAP_NET_ADMIN)"
else
  echo "[i] core-net not enabled (set ENABLE_CORE_NET_ADMIN=1)"
fi

echo "[+] systemd services started"
