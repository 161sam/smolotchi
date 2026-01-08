#!/usr/bin/env bash
set -euo pipefail

cd /

# Smolotchi Pi Zero Bootstrap
# Usage:
#   curl -sfL https://raw.githubusercontent.com/161sam/smolotchi/main/scripts/pi_zero/bootstrap.sh | \
#     sudo bash -s -- --repo "https://github.com/161sam/smolotchi.git" --branch main
#
# Optional:
#   --user smolotchi
#   --with-display
#   --enable-sudo (adds user to sudo group)
#   --unit-mode system|user   (default: system)

REPO_URL=""
BRANCH="main"
USER_NAME="smolotchi"
WITH_DISPLAY=0
ENABLE_SUDO=0
UNIT_MODE="system"

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
    --unit-mode)
      UNIT_MODE="$2"
      shift 2
      ;;
    -h|--help)
      echo "Usage: sudo $0 --repo <git-url> [--branch main] [--user smolotchi] [--with-display] [--enable-sudo] [--unit-mode system|user]"
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

if [[ "$UNIT_MODE" != "system" && "$UNIT_MODE" != "user" ]]; then
  echo "ERROR: --unit-mode must be 'system' or 'user' (got: $UNIT_MODE)"
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

SMOLO_HOME="/home/$USER_NAME"
SMOLO_REPO="$SMOLO_HOME/smolotchi"

echo "[4/9] create dirs and permissions"
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi/artifacts
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi
install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi/locks
install -d -m 0755 /etc/smolotchi

echo "[5/9] clone/update repo -> $SMOLO_REPO"
if [[ ! -d "$SMOLO_REPO/.git" ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$SMOLO_REPO"
else
  cd "$SMOLO_REPO"
  git fetch --all
  git checkout "$BRANCH"
  git pull --ff-only
fi
chown -R "$USER_NAME:$USER_NAME" "$SMOLO_REPO"

echo "[6/9] create venv + install editable"
sudo -u "$USER_NAME" bash -lc "
  cd '$SMOLO_REPO'
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -U pip
  pip install -e .
"

echo "[7/9] install config + env"
if [[ ! -f /etc/smolotchi/config.toml ]]; then
  if [[ -f "$SMOLO_REPO/contrib/pi_zero/config.toml" ]]; then
    cp "$SMOLO_REPO/contrib/pi_zero/config.toml" /etc/smolotchi/config.toml
  else
    cp "$SMOLO_REPO/config.toml" /etc/smolotchi/config.toml
  fi
fi

cat >/etc/smolotchi/env <<ENV
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks
SMOLOTCHI_DEFAULT_TAG=lab-approved
SMOLOTCHI_DISPLAY_DRYRUN=0
ENV
chmod 0644 /etc/smolotchi/env

# Stable CLI entrypoint used by systemd units
install -m 0755 /dev/stdin /usr/local/bin/smolotchi <<SH
#!/usr/bin/env bash
set -euo pipefail
exec "$SMOLO_REPO/.venv/bin/python" -m smolotchi.cli "\$@"
SH

systemctl_user() {
  local uid
  uid="$(id -u "$USER_NAME")"
  sudo -u "$USER_NAME" env "XDG_RUNTIME_DIR=/run/user/$uid" systemctl --user "$@"
}

echo "[8/9] install systemd units"

if [[ "$UNIT_MODE" == "system" ]]; then
  cat > /etc/systemd/system/smolotchi-core.service <<UNIT
[Unit]
Description=Smolotchi Core (WiFi / LAN / Tools Engine)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$SMOLO_REPO
EnvironmentFile=/etc/smolotchi/env
ExecStart=/usr/local/bin/smolotchi core
Restart=always
RestartSec=5

AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN
NoNewPrivileges=true

PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=/var/lib/smolotchi /run/smolotchi
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

  cat > /etc/systemd/system/smolotchi-web.service <<UNIT
[Unit]
Description=Smolotchi Web UI
After=network-online.target smolotchi-core.service
Wants=network-online.target
Requires=smolotchi-core.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$SMOLO_REPO
EnvironmentFile=/etc/smolotchi/env
ExecStart=/usr/local/bin/smolotchi web
Restart=always
RestartSec=5

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=/var/lib/smolotchi

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

  cat > /etc/systemd/system/smolotchi-ai.service <<UNIT
[Unit]
Description=Smolotchi AI Worker
After=network-online.target smolotchi-core.service
Wants=network-online.target
Requires=smolotchi-core.service

[Service]
Type=simple
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$SMOLO_REPO
EnvironmentFile=/etc/smolotchi/env
ExecStart=/usr/local/bin/smolotchi ai --loop --log-level INFO
Restart=always
RestartSec=10

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=false
ReadWritePaths=/var/lib/smolotchi

StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
UNIT

  # Use packaged prune units (they are now fixed & stable)
  install -m 0644 "$SMOLO_REPO/packaging/systemd/smolotchi-prune.service" /etc/systemd/system/smolotchi-prune.service
  install -m 0644 "$SMOLO_REPO/packaging/systemd/smolotchi-prune.timer"   /etc/systemd/system/smolotchi-prune.timer

  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    install -m 0644 "$SMOLO_REPO/packaging/systemd/smolotchi-display.service" /etc/systemd/system/smolotchi-display.service
  fi

  systemctl daemon-reload

else
  # user-mode
  loginctl enable-linger "$USER_NAME"

  sudo -u "$USER_NAME" mkdir -p "$SMOLO_HOME/.config/systemd/user"
  sudo -u "$USER_NAME" mkdir -p "$SMOLO_HOME/.config/smolotchi"

  # env for user-units
  install -m 0644 -o "$USER_NAME" -g "$USER_NAME" /etc/smolotchi/env "$SMOLO_HOME/.config/smolotchi/env"

  cat > "$SMOLO_HOME/.config/systemd/user/smolotchi-core.service" <<UNIT
[Unit]
Description=Smolotchi Core (User)
After=default.target

[Service]
Type=simple
WorkingDirectory=$SMOLO_REPO
EnvironmentFile=%h/.config/smolotchi/env
ExecStart=/usr/local/bin/smolotchi core
Restart=always
RestartSec=5

AmbientCapabilities=CAP_NET_RAW CAP_NET_ADMIN
CapabilityBoundingSet=CAP_NET_RAW CAP_NET_ADMIN
NoNewPrivileges=true

[Install]
WantedBy=default.target
UNIT

  cat > "$SMOLO_HOME/.config/systemd/user/smolotchi-web.service" <<UNIT
[Unit]
Description=Smolotchi Web UI (User)
After=smolotchi-core.service
Requires=smolotchi-core.service

[Service]
Type=simple
WorkingDirectory=$SMOLO_REPO
EnvironmentFile=%h/.config/smolotchi/env
ExecStart=/usr/local/bin/smolotchi web
Restart=always
RestartSec=5
NoNewPrivileges=true

[Install]
WantedBy=default.target
UNIT

  cat > "$SMOLO_HOME/.config/systemd/user/smolotchi-ai.service" <<UNIT
[Unit]
Description=Smolotchi AI Worker (User)
After=smolotchi-core.service
Requires=smolotchi-core.service

[Service]
Type=simple
WorkingDirectory=$SMOLO_REPO
EnvironmentFile=%h/.config/smolotchi/env
ExecStart=/usr/local/bin/smolotchi ai --loop --log-level INFO
Restart=always
RestartSec=10
NoNewPrivileges=true

[Install]
WantedBy=default.target
UNIT

  chown -R "$USER_NAME:$USER_NAME" "$SMOLO_HOME/.config/systemd/user" "$SMOLO_HOME/.config/smolotchi"
  systemctl_user daemon-reload
fi

echo "[9/9] enable + start"
if [[ "$UNIT_MODE" == "system" ]]; then
  systemctl enable --now smolotchi-core.service
  systemctl enable --now smolotchi-web.service
  systemctl enable --now smolotchi-ai.service
  systemctl enable --now smolotchi-prune.timer

  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    systemctl enable --now smolotchi-display.service
  fi

  echo "DONE (system-mode)."
  echo "Check:"
  echo "  systemctl status smolotchi-core smolotchi-web smolotchi-ai --no-pager"
  echo "  journalctl -u smolotchi-core -n 120 --no-pager"

else
  systemctl_user enable --now smolotchi-core.service
  systemctl_user enable --now smolotchi-web.service
  systemctl_user enable --now smolotchi-ai.service

  echo "DONE (user-mode)."
  uid="$(id -u "$USER_NAME")"
  echo "Check:"
  echo "  sudo -u $USER_NAME env XDG_RUNTIME_DIR=/run/user/$uid systemctl --user status smolotchi-core smolotchi-web smolotchi-ai --no-pager"
fi
