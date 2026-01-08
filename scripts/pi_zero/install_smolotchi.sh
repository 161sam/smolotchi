#!/usr/bin/env bash
set -euo pipefail

echo "[+] Installing Smolotchi (pi_zero bootstrap)"

REPO_URL="${REPO_URL:-https://github.com/161sam/smolotchi.git}"
BRANCH="${BRANCH:-main}"
USER_NAME="${USER_NAME:-smolotchi}"

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

apt-get update
apt-get install -y --no-install-recommends \
  git python3 python3-venv python3-pip ca-certificates curl

id "$USER_NAME" >/dev/null 2>&1 || useradd -m -s /bin/bash "$USER_NAME"

SMOLO_HOME="/home/$USER_NAME"
SMOLO_REPO="$SMOLO_HOME/smolotchi"

# clone / update repo
if [[ ! -d "$SMOLO_REPO/.git" ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$SMOLO_REPO"
else
  cd "$SMOLO_REPO"
  git fetch --all
  git checkout "$BRANCH"
  git pull --ff-only
fi

chown -R "$USER_NAME:$USER_NAME" "$SMOLO_REPO"

# venv + editable install
sudo -u "$USER_NAME" bash -lc "
  cd '$SMOLO_REPO'
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -U pip wheel
  pip install -e .
"

# install wrapper (for CLI + systemd ExecStart=/usr/local/bin/smolotchi)
if [[ -f "$SMOLO_REPO/packaging/bin/smolotchi" ]]; then
  install -m 0755 "$SMOLO_REPO/packaging/bin/smolotchi" /usr/local/bin/smolotchi
else
  echo "warn: wrapper not found at $SMOLO_REPO/packaging/bin/smolotchi"
  echo "      systemd units will fail unless you add the wrapper to packaging/bin/"
fi

# state/runtime dirs expected by hardening
install -d -m 0775 /var/lib/smolotchi /var/lib/smolotchi/artifacts
install -d -m 0775 /run/smolotchi /run/smolotchi/locks
chown -R "$USER_NAME:$USER_NAME" /var/lib/smolotchi /run/smolotchi

# env + config
install -d -m 0755 /etc/smolotchi

cat > /etc/smolotchi/env <<EOF
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks
SMOLOTCHI_DEFAULT_TAG=lab-approved
EOF
chmod 0644 /etc/smolotchi/env

if [[ -f "$SMOLO_REPO/config.toml" && ! -f /etc/smolotchi/config.toml ]]; then
  cp "$SMOLO_REPO/config.toml" /etc/smolotchi/config.toml
  chmod 0644 /etc/smolotchi/config.toml
fi

echo "[+] Smolotchi installed to $SMOLO_REPO"
echo "Next:"
echo "  sudo $SMOLO_REPO/scripts/pi_zero/install_systemd.sh"
