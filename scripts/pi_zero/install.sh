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

cd /

python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install -U pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements/base.txt" -r "$PROJECT_DIR/requirements/pi_zero.txt"
"$VENV_DIR/bin/pip" install -e "$PROJECT_DIR"

mkdir -p "$ENV_DIR"
if [[ ! -f "$ENV_FILE" ]]; then
  cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
fi

install -m 0755 /dev/stdin /usr/local/bin/smolotchi <<SH
#!/usr/bin/env bash
set -euo pipefail
exec "$VENV_DIR/bin/python" -m smolotchi.cli "\$@"
SH

install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-core.service" /etc/systemd/system/smolotchi-core.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-ai.service"   /etc/systemd/system/smolotchi-ai.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-web.service"  /etc/systemd/system/smolotchi-web.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-display.service" /etc/systemd/system/smolotchi-display.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.service" /etc/systemd/system/smolotchi-prune.service
install -m 0644 "$PROJECT_DIR/packaging/systemd/smolotchi-prune.timer"   /etc/systemd/system/smolotchi-prune.timer

systemctl daemon-reexec
systemctl daemon-reload

cat <<'EOM'
Done.

Enable autostart:
  sudo systemctl enable smolotchi-core smolotchi-ai smolotchi-web smolotchi-prune.timer

Start now:
  sudo systemctl start smolotchi-core smolotchi-ai smolotchi-web smolotchi-prune.timer

Optional display (enable/start):
  sudo systemctl enable smolotchi-display
  sudo systemctl start smolotchi-display
EOM
