#!/usr/bin/env bash
set -euo pipefail

cd ~

echo "[+] Installing Smolotchi"

git clone https://github.com/161sam/smolotchi.git
cd smolotchi

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
pip install -e .

sudo mkdir -p /etc/smolotchi
sudo tee /etc/smolotchi/env >/dev/null <<'EOF'
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/home/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_DEFAULT_TAG=lab-approved
EOF

cp config.toml /home/smolotchi/config.toml || true

echo "[+] Smolotchi installed"
