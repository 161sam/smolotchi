#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo "[+] Installing systemd units"

cp "$PROJECT_DIR"/packaging/systemd/*.service /etc/systemd/system/
cp "$PROJECT_DIR"/packaging/systemd/*.timer /etc/systemd/system/ || true
install -m 0755 "$PROJECT_DIR"/packaging/bin/smolotchi /usr/local/bin/smolotchi

install_dropin() {
  local unit="$1"
  local src="$2"
  local dst_dir="/etc/systemd/system/${unit}.d"

  install -d -m 0755 "$dst_dir"
  install -m 0644 "$PROJECT_DIR"/packaging/systemd/dropins/"$src" "$dst_dir/$src"
}

install_dropin_dir() {
  local unit="$1"
  local src_dir="$PROJECT_DIR/packaging/systemd/dropins/${unit}.d"
  local dst_dir="/etc/systemd/system/${unit}.d"

  if [[ ! -d "$src_dir" ]]; then
    return
  fi

  install -d -m 0755 "$dst_dir"
  for dropin in "$src_dir"/*.conf; do
    if [[ -f "$dropin" ]]; then
      install -m 0644 "$dropin" "$dst_dir/$(basename "$dropin")"
    fi
  done
}

install_dropin smolotchi-core.service 10-hardening.conf
install_dropin smolotchi-core-net.service 10-hardening.conf
install_dropin smolotchi-web.service 10-hardening.conf
install_dropin smolotchi-ai.service 10-hardening.conf
install_dropin smolotchi-display.service 10-hardening.conf
install_dropin smolotchi-prune.service 10-hardening.conf
install_dropin smolotchi-prune.service 10-hardening-prune.conf
install_dropin smolotchi-core.service 11-protect-home.conf
install_dropin smolotchi-core-net.service 11-protect-home.conf
install_dropin smolotchi-web.service 11-protect-home.conf
install_dropin smolotchi-ai.service 11-protect-home.conf
install_dropin smolotchi-prune.service 11-protect-home.conf
install_dropin smolotchi-core.service 12-restart-protection.conf
install_dropin smolotchi-core-net.service 12-restart-protection.conf
install_dropin smolotchi-web.service 12-restart-protection.conf
install_dropin smolotchi-ai.service 12-restart-protection.conf
install_dropin smolotchi-display.service 12-restart-protection.conf
install_dropin smolotchi-core.service 15-runtime-dirs.conf
install_dropin smolotchi-core-net.service 15-runtime-dirs.conf
install_dropin smolotchi-web.service 15-runtime-dirs.conf
install_dropin smolotchi-ai.service 15-runtime-dirs.conf
install_dropin smolotchi-display.service 15-runtime-dirs.conf
install_dropin smolotchi-prune.service 15-runtime-dirs.conf
install_dropin smolotchi-web.service 20-cap-defaults.conf
install_dropin smolotchi-ai.service 20-cap-defaults.conf
install_dropin smolotchi-display.service 20-cap-defaults.conf
install_dropin smolotchi-prune.service 20-cap-defaults.conf
install_dropin_dir smolotchi-core.service
install_dropin_dir smolotchi-core-net.service
install_dropin_dir smolotchi-web.service
install_dropin_dir smolotchi-ai.service
install_dropin_dir smolotchi-display.service
install_dropin_dir smolotchi-prune.service

install -d -m 0755 /etc/tmpfiles.d
install -m 0644 "$PROJECT_DIR/packaging/systemd/tmpfiles.d/smolotchi.conf" /etc/tmpfiles.d/smolotchi.conf
systemd-tmpfiles --create /etc/tmpfiles.d/smolotchi.conf

# optional:
# install_dropin smolotchi-core.service 20-homedir-readonly.conf

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
  systemctl disable --now smolotchi-core-net || true
  echo "[i] core-net not enabled (set ENABLE_CORE_NET_ADMIN=1)"
fi

if [[ "${ENABLE_DISPLAY:-0}" == "1" ]]; then
  systemctl enable --now smolotchi-display
  echo "[+] display enabled"
else
  echo "[i] display not enabled (set ENABLE_DISPLAY=1)"
fi

echo "[+] systemd services started"
