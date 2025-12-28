#!/usr/bin/env bash
set -euo pipefail

# Smolotchi Pi Zero Bootstrap
# Usage:
#   sudo ./scripts/pi_zero/bootstrap.sh --repo "https://github.com/<you>/smolotchi.git" --branch main
# Optional:
#   --user smolotchi
#   --with-display
#   --enable-sudo (adds user to sudo group)

REPO_URL=""
BRANCH="main"
USER_NAME="smolotchi"
WITH_DISPLAY=0
ENABLE_SUDO=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO_URL="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --user)
      USER_NAME="$2"
      shift 2
      ;;
    --with-display)
      WITH_DISPLAY=1
      shift
      ;;
    --enable-sudo)
      ENABLE_SUDO=1
      shift
      ;;
    -h|--help)
      echo "Usage: sudo $0 --repo <git-url> [--branch main] [--user smolotchi] [--with-display] [--enable-sudo]"
      exit 0
      ;;
    *)
      echo "Unknown arg: $1"
      exit 1
      ;;
  esac
done

if [[ -z "$REPO_URL" ]]; then
  echo "ERROR: --repo is required"
  exit 1
fi

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

echo "[1/9] apt update + packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
  build-essential \
  git ca-certificates curl \
  python3 python3-venv python3-pip \
  sqlite3 \
  iw wireless-tools rfkill iproute2 \
  systemd \
  procps

echo "[2/9] enable ssh"
apt-get install -y --no-install-recommends openssh-server
systemctl enable --now ssh

echo "[3/9] create user: $USER_NAME (if missing)"
if ! id "$USER_NAME" >/dev/null 2>&1; then
  useradd -m -s /bin/bash "$USER_NAME"
fi
if [[ "$ENABLE_SUDO" -eq 1 ]]; then
  usermod -aG sudo "$USER_NAME"
fi

echo "[4/9] create dirs and permissions"
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi/artifacts
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi/locks
install -d -m 0755 /etc/smolotchi

echo "[5/9] clone/update repo -> /opt/smolotchi"
if [[ ! -d /opt/smolotchi/.git ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" /opt/smolotchi
else
  cd /opt/smolotchi
  git fetch --all
  git checkout "$BRANCH"
  git pull --ff-only
fi
chown -R "$USER_NAME:$USER_NAME" /opt/smolotchi

echo "[6/9] create venv + install editable"
sudo -u "$USER_NAME" bash -lc "
  cd /opt/smolotchi
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -U pip
  pip install -e .
"

echo "[7/9] install config + env"
if [[ ! -f /etc/smolotchi/config.toml ]]; then
  if [[ -f /opt/smolotchi/contrib/pi_zero/config.toml ]]; then
    cp /opt/smolotchi/contrib/pi_zero/config.toml /etc/smolotchi/config.toml
  else
    cp /opt/smolotchi/config.toml /etc/smolotchi/config.toml
  fi
fi

cat >/etc/smolotchi/smolotchi.env <<'ENV'
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks
ENV

chmod 0644 /etc/smolotchi/smolotchi.env

install -m 0755 /dev/stdin /usr/local/bin/smolotchi <<'SH'
#!/usr/bin/env bash
exec /opt/smolotchi/.venv/bin/python -m smolotchi.cli "$@"
SH

echo "[8/9] install systemd units"
install -m 0644 /opt/smolotchi/packaging/systemd/smolotchi-core.service /etc/systemd/system/smolotchi-core.service
install -m 0644 /opt/smolotchi/packaging/systemd/smolotchi-web.service /etc/systemd/system/smolotchi-web.service
install -m 0644 /opt/smolotchi/packaging/systemd/smolotchi-ai-worker.service /etc/systemd/system/smolotchi-ai-worker.service

if [[ "$WITH_DISPLAY" -eq 1 ]]; then
  install -m 0644 /opt/smolotchi/packaging/systemd/smolotchi-display.service /etc/systemd/system/smolotchi-display.service
fi

systemctl daemon-reload

echo "[9/9] enable + start"
systemctl enable --now smolotchi-core.service
systemctl enable --now smolotchi-web.service
systemctl enable --now smolotchi-ai-worker.service

if [[ "$WITH_DISPLAY" -eq 1 ]]; then
  systemctl enable --now smolotchi-display.service
fi

echo "DONE."
echo "Check:"
echo "  systemctl status smolotchi-core smolotchi-web smolotchi-ai-worker --no-pager"
echo "  journalctl -u smolotchi-core -f"
