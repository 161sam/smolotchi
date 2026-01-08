#!/usr/bin/env bash
set -euo pipefail

cd /

echo "[+] Smolotchi Pi Zero Bootstrap (base)"

apt update
apt install -y \
  git curl wget ca-certificates \
  python3 python3-venv python3-pip \
  sqlite3 jq \
  nmap \
  tcpdump \
  iw wireless-tools rfkill \
  systemd-timesyncd

apt install -y bettercap || echo "[!] bettercap not available via apt"

systemctl enable --now ssh

id smolotchi >/dev/null 2>&1 || useradd -m -s /bin/bash smolotchi

mkdir -p /var/lib/smolotchi/{artifacts,logs}
mkdir -p /run/smolotchi/locks
chown -R smolotchi:smolotchi /var/lib/smolotchi /run/smolotchi

sysctl -w net.ipv4.ip_forward=1 || true

echo "[+] Bootstrap base done"
