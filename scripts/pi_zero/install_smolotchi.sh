#!/usr/bin/env bash
set -euo pipefail

echo "[+] Installing Smolotchi (simple)"

REPO_URL="${REPO_URL:-https://github.com/161sam/smolotchi.git}"
BRANCH="${BRANCH:-main}"
USER_NAME="${USER_NAME:-smolotchi}"

if [[ $EUID -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

cd /

apt-get update
apt-get install -y --no-install-recommends git python3 python3-venv python3-pip ca-certificates curl

id "$USER_NAME" >/dev/null 2>&1 || useradd -m -s /bin/bash "$USER_NAME"

SMOLO_HOME="/home/$USER_NAME"
SMOLO_REPO="$SMOLO_HOME/smolotchi"

if [[ ! -d "$SMOLO_REPO/.git" ]]; then
  git clone --branch "$BRANCH" "$REPO_URL" "$SMOLO_REPO"
else
  cd "$SMOLO_REPO"
  git fetch --all
  git checkout "$BRANCH"
  git pull --ff-only
fi
chown -R "$USER_NAME:$USER_NAME" "$SMOLO_REPO"

sudo -u "$USER_NAME" bash -lc "
  cd '$SMOLO_REPO'
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -U pip wheel
  pip install -e .
"

sudo mkdir -p /etc/smolotchi
sudo tee /etc/smolotchi/env >/dev/null <<EOF
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks
SMOLOTCHI_DEFAULT_TAG=lab-approved
EOF

if [[ -f "$SMOLO_REPO/config.toml" && ! -f /etc/smolotchi/config.toml ]]; then
  sudo cp "$SMOLO_REPO/config.toml" /etc/smolotchi/config.toml
fi

echo "[+] Smolotchi installed to $SMOLO_REPO"
