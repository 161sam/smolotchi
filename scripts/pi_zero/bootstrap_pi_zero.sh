#!/usr/bin/env bash
set -euo pipefail

echo "[DEPRECATED] scripts/pi_zero/bootstrap_pi_zero.sh is deprecated. Use scripts/deploy.sh instead." >&2
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
exec "${ROOT_DIR}/deploy.sh" "$@"
