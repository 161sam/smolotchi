#!/usr/bin/env bash
set -euo pipefail

# Smolotchi FULL uninstall / wipe
# - Stops/disables services, removes units/dropins, removes /opt deploy, /etc config,
#   state dirs, wrapper, tempfiles.
# - Optional: remove user+group "smolotchi" (default: keep).
#
# Usage:
#   sudo ./scripts/uninstall_smolotchi.sh --apply
#   sudo ./scripts/uninstall_smolotchi.sh --apply --remove-user
#   sudo ./scripts/uninstall_smolotchi.sh --dry-run
#
# Safety:
#   Requires --apply to actually delete anything.

APPLY=0
REMOVE_USER=0
DRYRUN=0

log() { echo "[uninstall] $*"; }
run() {
  if [[ "$DRYRUN" == "1" ]]; then
    echo "+ $*"
  else
    eval "$@"
  fi
}

usage() {
  cat <<'USAGE'
Smolotchi FULL uninstall / wipe.

Options:
  --apply           Actually perform removals (required to delete anything)
  --dry-run         Print what would be removed
  --remove-user     Also delete linux user+group "smolotchi" (default: keep user)
  --help            Show this help

Examples:
  sudo ./scripts/uninstall_smolotchi.sh --dry-run
  sudo ./scripts/uninstall_smolotchi.sh --apply
  sudo ./scripts/uninstall_smolotchi.sh --apply --remove-user
USAGE
}

if [[ "${EUID:-0}" -ne 0 ]]; then
  echo "error: run as root (sudo)."
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift;;
    --dry-run) DRYRUN=1; shift;;
    --remove-user) REMOVE_USER=1; shift;;
    -h|--help) usage; exit 0;;
    *)
      echo "error: unknown arg: $1"
      usage
      exit 2
      ;;
  esac
done

if [[ "$DRYRUN" == "1" ]]; then
  APPLY=0
fi

if [[ "$APPLY" != "1" && "$DRYRUN" != "1" ]]; then
  echo "Refusing to run without --apply or --dry-run."
  echo "Tip: run with --dry-run first, then --apply."
  exit 2
fi

UNIT_FILES=(
  /etc/systemd/system/smolotchi-core.service
  /etc/systemd/system/smolotchi-core-net.service
  /etc/systemd/system/smolotchi-web.service
  /etc/systemd/system/smolotchi-ai.service
  /etc/systemd/system/smolotchi-ai-worker.service
  /etc/systemd/system/smolotchi-display.service
  /etc/systemd/system/smolotchi-prune.service
  /etc/systemd/system/smolotchi-prune.timer
)

UNIT_DIRS=(
  /etc/systemd/system/smolotchi-core.service.d
  /etc/systemd/system/smolotchi-core-net.service.d
  /etc/systemd/system/smolotchi-web.service.d
  /etc/systemd/system/smolotchi-ai.service.d
  /etc/systemd/system/smolotchi-ai-worker.service.d
  /etc/systemd/system/smolotchi-display.service.d
  /etc/systemd/system/smolotchi-prune.service.d
)

# best-effort list of unit names (some may not exist on older installs)
UNITS=(
  smolotchi-core
  smolotchi-core-net
  smolotchi-web
  smolotchi-ai
  smolotchi-ai-worker
  smolotchi-display
  smolotchi-prune.timer
  smolotchi-prune
)

log "Mode: $( [[ "$DRYRUN" == "1" ]] && echo "DRY-RUN" || echo "APPLY" )"
log "remove-user: $REMOVE_USER"

log "Stopping units (best-effort)…"
for u in "${UNITS[@]}"; do
  run "systemctl stop \"$u\" 2>/dev/null || true"
done

log "Disabling units (best-effort)…"
for u in "${UNITS[@]}"; do
  run "systemctl disable --now \"$u\" 2>/dev/null || true"
done

log "Resetting failed state…"
run "systemctl reset-failed smolotchi-core smolotchi-web smolotchi-ai smolotchi-ai-worker smolotchi-display smolotchi-core-net smolotchi-prune 2>/dev/null || true"

log "Removing unit files…"
for f in "${UNIT_FILES[@]}"; do
  run "rm -f \"$f\""
done

log "Removing drop-in dirs…"
for d in "${UNIT_DIRS[@]}"; do
  run "rm -rf \"$d\""
done

log "Removing tmpfiles config…"
run "rm -f /etc/tmpfiles.d/smolotchi.conf"
run "systemd-tmpfiles --remove /etc/tmpfiles.d/smolotchi.conf 2>/dev/null || true"

log "Removing wrapper /usr/local/bin/smolotchi …"
run "rm -f /usr/local/bin/smolotchi"

log "Removing config /etc/smolotchi …"
run "rm -rf /etc/smolotchi"

log "Removing state /var/lib/smolotchi …"
run "rm -rf /var/lib/smolotchi"

log "Removing runtime /run/smolotchi …"
run "rm -rf /run/smolotchi"

log "Removing /opt deploy (/opt/smolotchi) …"
run "rm -rf /opt/smolotchi"

log "Removing any leftover home checkout (if exists) …"
if id -u smolotchi >/dev/null 2>&1; then
  # very conservative: remove only known repo folder name in home if present
  HOME_DIR="$(getent passwd smolotchi | cut -d: -f6)"
  if [[ -n "${HOME_DIR:-}" && -d "$HOME_DIR" ]]; then
    run "rm -rf \"$HOME_DIR/smolotchi\""
    run "rm -rf \"$HOME_DIR/.cache/pip\" \"$HOME_DIR/.cache/pip-tools\" 2>/dev/null || true"
  fi
fi

log "Reloading systemd…"
run "systemctl daemon-reload"
run "systemctl daemon-reexec 2>/dev/null || true"

if [[ "$REMOVE_USER" == "1" ]]; then
  log "Removing user+group smolotchi (best-effort)…"
  if id -u smolotchi >/dev/null 2>&1; then
    # remove user and home dir
    run "userdel -r smolotchi 2>/dev/null || userdel smolotchi 2>/dev/null || true"
  fi
  if getent group smolotchi >/dev/null 2>&1; then
    run "groupdel smolotchi 2>/dev/null || true"
  fi
else
  log "Keeping user 'smolotchi' (no --remove-user)."
fi

log "Done."

if [[ "$DRYRUN" == "1" ]]; then
  log "This was a DRY-RUN. Re-run with: sudo $0 --apply"
fi
