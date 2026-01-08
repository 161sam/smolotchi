#!/usr/bin/env bash
set -euo pipefail

echo "[+] Installing systemd units"

cp packaging/systemd/*.service /etc/systemd/system/
cp packaging/systemd/*.timer /etc/systemd/system/ || true
install -m 0755 packaging/bin/smolotchi /usr/local/bin/smolotchi

install -d /etc/systemd/system/smolotchi-core.service.d
install -d /etc/systemd/system/smolotchi-core-net.service.d
install -d /etc/systemd/system/smolotchi-web.service.d
install -d /etc/systemd/system/smolotchi-ai.service.d
install -d /etc/systemd/system/smolotchi-prune.service.d

install -m 0644 packaging/systemd/dropins/10-hardening.conf /etc/systemd/system/smolotchi-core.service.d/10-hardening.conf
install -m 0644 packaging/systemd/dropins/10-hardening.conf /etc/systemd/system/smolotchi-core-net.service.d/10-hardening.conf
install -m 0644 packaging/systemd/dropins/10-hardening.conf /etc/systemd/system/smolotchi-web.service.d/10-hardening.conf
install -m 0644 packaging/systemd/dropins/10-hardening.conf /etc/systemd/system/smolotchi-ai.service.d/10-hardening.conf
install -m 0644 packaging/systemd/dropins/10-hardening-prune.conf /etc/systemd/system/smolotchi-prune.service.d/10-hardening.conf

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

if [[ "${ENABLE_DISPLAY:-0}" == "1" ]]; then
  systemctl enable --now smolotchi-display
  echo "[+] display enabled"
else
  echo "[i] display not enabled (set ENABLE_DISPLAY=1)"
fi

echo "[+] systemd services started"
