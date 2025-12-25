#!/usr/bin/env bash
set -euo pipefail

if [[ ! -d ".venv" ]]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -U pip
pip install -e .

export SMO_AI_WORKER=1

python -m smolotchi.api.web
