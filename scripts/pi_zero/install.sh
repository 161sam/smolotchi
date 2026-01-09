#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
PROJECT_DIR=${PROJECT_DIR:-"$ROOT_DIR"}
VENV_DIR=${VENV_DIR:-"$PROJECT_DIR/.venv"}
ENV_DIR=${ENV_DIR:-"/etc/smolotchi"}
ENV_FILE=${ENV_FILE:-"$ENV_DIR/env"}

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -U pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements/base.txt" -r "$PROJECT_DIR/requirements/pi_zero.txt"
"$VENV_DIR/bin/pip" install -e "$PROJECT_DIR"

mkdir -p "$ENV_DIR"
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
fi

install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-core.service" /etc/systemd/system/smolotchi-core.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-core-net.service" /etc/systemd/system/smolotchi-core-net.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-ai.service" /etc/systemd/system/smolotchi-ai.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-display.service" /etc/systemd/system/smolotchi-display.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-web.service" /etc/systemd/system/smolotchi-web.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.service" /etc/systemd/system/smolotchi-prune.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.timer" /etc/systemd/system/smolotchi-prune.timer
install -m 0755 "$PROJECT_DIR/packaging/bin/smolotchi" /usr/local/bin/smolotchi

install -d /etc/systemd/system/smolotchi-core.service.d
install -d /etc/systemd/system/smolotchi-core-net.service.d
install -d /etc/systemd/system/smolotchi-web.service.d
install -d /etc/systemd/system/smolotchi-ai.service.d
install -d /etc/systemd/system/smolotchi-display.service.d
install -d /etc/systemd/system/smolotchi-prune.service.d

install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/10-hardening.conf" /etc/systemd/system/smolotchi-core.service.d/10-hardening.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/10-hardening.conf" /etc/systemd/system/smolotchi-core-net.service.d/10-hardening.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/10-hardening.conf" /etc/systemd/system/smolotchi-web.service.d/10-hardening.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/10-hardening.conf" /etc/systemd/system/smolotchi-ai.service.d/10-hardening.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/10-hardening.conf" /etc/systemd/system/smolotchi-display.service.d/10-hardening.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/10-hardening.conf" /etc/systemd/system/smolotchi-prune.service.d/10-hardening.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/12-restart-protection.conf" /etc/systemd/system/smolotchi-core.service.d/12-restart-protection.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/12-restart-protection.conf" /etc/systemd/system/smolotchi-core-net.service.d/12-restart-protection.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/12-restart-protection.conf" /etc/systemd/system/smolotchi-web.service.d/12-restart-protection.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/12-restart-protection.conf" /etc/systemd/system/smolotchi-ai.service.d/12-restart-protection.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/12-restart-protection.conf" /etc/systemd/system/smolotchi-display.service.d/12-restart-protection.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/15-runtime-dirs.conf" /etc/systemd/system/smolotchi-core.service.d/15-runtime-dirs.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/15-runtime-dirs.conf" /etc/systemd/system/smolotchi-core-net.service.d/15-runtime-dirs.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/15-runtime-dirs.conf" /etc/systemd/system/smolotchi-web.service.d/15-runtime-dirs.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/15-runtime-dirs.conf" /etc/systemd/system/smolotchi-ai.service.d/15-runtime-dirs.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/15-runtime-dirs.conf" /etc/systemd/system/smolotchi-display.service.d/15-runtime-dirs.conf
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/15-runtime-dirs.conf" /etc/systemd/system/smolotchi-prune.service.d/15-runtime-dirs.conf

install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/smolotchi-core.service.d/"*.conf /etc/systemd/system/smolotchi-core.service.d/
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/smolotchi-core-net.service.d/"*.conf /etc/systemd/system/smolotchi-core-net.service.d/
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/smolotchi-web.service.d/"*.conf /etc/systemd/system/smolotchi-web.service.d/
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/smolotchi-ai.service.d/"*.conf /etc/systemd/system/smolotchi-ai.service.d/
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/smolotchi-display.service.d/"*.conf /etc/systemd/system/smolotchi-display.service.d/
install -m 0644 "$PROJECT_DIR/packaging/systemd/dropins/smolotchi-prune.service.d/"*.conf /etc/systemd/system/smolotchi-prune.service.d/

systemctl daemon-reload

cat <<'EOM'
Done.

Enable UI-only mode:
  sudo systemctl enable --now smolotchi-core smolotchi-ai smolotchi-display

Optional web UI:
  sudo systemctl enable --now smolotchi-web
EOM
