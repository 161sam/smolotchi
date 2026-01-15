#!/usr/bin/env bash
set -euo pipefail

# Smolotchi: single canonical bootstrap + deploy script
# - root-only
# - deploys repo checkout to: /opt/smolotchi/current
# - venv lives in:           /opt/smolotchi/current/.venv
# - config/env live in:      /etc/smolotchi/{config.toml,env}
# - state/runtime live in:   /var/lib/smolotchi + /run/smolotchi
#
# Usage (curl|bash):
#   curl -sfL https://raw.githubusercontent.com/<YOU>/<REPO>/main/scripts/deploy.sh | sudo bash -s -- --repo https://github.com/<YOU>/<REPO>.git --branch main --apply
#
# Usage (local repo):
#   sudo ./scripts/deploy.sh --apply
#
# Flags:
#   --repo <git-url>      (optional if running inside repo; required for curl|bash)
#   --branch <name>       (default: main)
#   --user <name>         (default: smolotchi)
#   --with-display        (install+enable display service)
#   --enable-sudo         (adds user to sudo group, only if created)
#   --enable-core-net     (enables smolotchi-core-net and disables smolotchi-core)
#   --skip-apt            (skip apt install step)
#   --apply               (actually perform changes; default is PREVIEW)
#   --force               (ignore some safety checks)
#   -h|--help

REPO_URL=""
BRANCH="main"
USER_NAME="smolotchi"
WITH_DISPLAY=0
ENABLE_SUDO=0
ENABLE_CORE_NET=0
SKIP_APT=0
APPLY=0
FORCE=0

MODE="PREVIEW"

log() { echo "[deploy] $*"; }
die() { echo "[deploy] ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_URL="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --user) USER_NAME="$2"; shift 2;;
    --with-display) WITH_DISPLAY=1; shift;;
    --enable-sudo) ENABLE_SUDO=1; shift;;
    --enable-core-net) ENABLE_CORE_NET=1; shift;;
    --skip-apt) SKIP_APT=1; shift;;
    --apply) APPLY=1; MODE="APPLY"; shift;;
    --force) FORCE=1; shift;;
    -h|--help)
      sed -n '1,80p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) die "Unknown arg: $1";;
  esac
done

[[ $EUID -eq 0 ]] || die "run as root (sudo)."

DEPLOY_ROOT="/opt/smolotchi"
DEPLOY_DIR="${DEPLOY_ROOT}/current"
VENV_DIR="${DEPLOY_DIR}/.venv"
ETC_DIR="/etc/smolotchi"
ENV_FILE="${ETC_DIR}/env"
CFG_FILE="${ETC_DIR}/config.toml"

SYSTEMD_DIR="/etc/systemd/system"
TMPFILES_DIR="/etc/tmpfiles.d"
TMPFILES_FILE="${TMPFILES_DIR}/smolotchi.conf"

# Units (expected to exist in repo under packaging/systemd)
UNITS=(
  "smolotchi-core.service"
  "smolotchi-core-net.service"
  "smolotchi-web.service"
  "smolotchi-ai.service"
  "smolotchi-prune.service"
  "smolotchi-prune.timer"
)
DISPLAY_UNIT="smolotchi-display.service"

# --- helpers
run() {
  if [[ "$APPLY" -eq 1 ]]; then
    "$@"
  else
    log "PREVIEW: $*"
  fi
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

ensure_apt() {
  if [[ "$SKIP_APT" -eq 1 ]]; then
    log "Skipping apt step (--skip-apt)."
    return
  fi

  export DEBIAN_FRONTEND=noninteractive
  log "apt update + base packages"
  run apt-get update
  run apt-get install -y --no-install-recommends \
    build-essential \
    git ca-certificates curl \
    python3 python3-venv python3-pip \
    sqlite3 \
    iw wireless-tools rfkill iproute2 \
    systemd procps \
    openssh-server

  # optional tools (best-effort)
  run bash -lc 'apt-get install -y --no-install-recommends jq nmap tcpdump || true'
  run bash -lc 'apt-get install -y --no-install-recommends bettercap || true'

  run systemctl enable --now ssh || true
}

ensure_user() {
  log "ensure user: ${USER_NAME}"
  if ! id "$USER_NAME" >/dev/null 2>&1; then
    run useradd -m -s /bin/bash "$USER_NAME"
    if [[ "$ENABLE_SUDO" -eq 1 ]]; then
      run usermod -aG sudo "$USER_NAME"
    fi
  fi
}

ensure_dirs() {
  log "ensure dirs (/var/lib, /run, /etc, /opt)"
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi/artifacts
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi/locks
  run install -d -m 0755 "$ETC_DIR"
  run install -d -m 0755 "$DEPLOY_ROOT"
}

detect_project_dir() {
  # If running inside repo: PROJECT_DIR is repo root (contains pyproject.toml)
  # Else (curl|bash): we will clone into /opt/smolotchi/current
  if [[ -f "./pyproject.toml" && -d "./smolotchi" && -d "./packaging" ]]; then
    echo "$(pwd)"
    return
  fi
  if [[ -z "$REPO_URL" ]]; then
    die "not running inside repo and --repo not provided (required for curl|bash)."
  fi
  echo ""
}

checkout_or_update_repo() {
  local project_dir="$1"
  if [[ -n "$project_dir" ]]; then
    log "Using local repo at: $project_dir"
    return 0
  fi

  require_cmd git
  log "clone/update repo -> ${DEPLOY_DIR}"
  if [[ ! -d "${DEPLOY_DIR}/.git" ]]; then
    run rm -rf "$DEPLOY_DIR" || true
    run git clone --branch "$BRANCH" "$REPO_URL" "$DEPLOY_DIR"
  else
    run bash -lc "cd '$DEPLOY_DIR' && git fetch --all && git checkout '$BRANCH' && git pull --ff-only"
  fi
}

install_venv_and_package() {
  log "create venv + pip install (requirements + editable)"
  run python3 -m venv "$VENV_DIR"
  run "$VENV_DIR/bin/pip" install -U pip wheel

  # requirements from repo layout
  run "$VENV_DIR/bin/pip" install -r "$DEPLOY_DIR/requirements/base.txt" -r "$DEPLOY_DIR/requirements/pi_zero.txt"
  run "$VENV_DIR/bin/pip" install -e "$DEPLOY_DIR"
}

install_config_and_env() {
  log "install /etc/smolotchi/config.toml + env"

  # config.toml: copy from repo if missing
  if [[ ! -f "$CFG_FILE" ]]; then
    if [[ -f "$DEPLOY_DIR/contrib/pi_zero/config.toml" ]]; then
      run install -m 0644 "$DEPLOY_DIR/contrib/pi_zero/config.toml" "$CFG_FILE"
    else
      run install -m 0644 "$DEPLOY_DIR/config.toml" "$CFG_FILE"
    fi
    run chown root:root "$CFG_FILE"
  else
    log "config exists: $CFG_FILE (keeping)"
  fi

  # env: create/update canonical env file
  # Always enforce SMOLOTCHI_CONFIG -> /etc/smolotchi/config.toml to avoid ProtectHome issues
  local tmp_env
  tmp_env="$(mktemp)"
  cat >"$tmp_env" <<EOF
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks
SMOLOTCHI_DEFAULT_TAG=lab-approved
SMOLOTCHI_DISPLAY_DRYRUN=0
EOF

  if [[ ! -f "$ENV_FILE" ]]; then
    run install -m 0644 "$tmp_env" "$ENV_FILE"
  else
    # merge strategy: keep existing extra lines, but enforce keys above
    # simple approach: replace matching keys, append missing keys
    run bash -lc "
      set -euo pipefail
      cp '$ENV_FILE' '${ENV_FILE}.bak'
      while IFS= read -r line; do
        key=\${line%%=*}
        if grep -q \"^\${key}=\" '$ENV_FILE'; then
          sed -i \"s|^\${key}=.*|\${line}|\" '$ENV_FILE'
        else
          echo \"\${line}\" >> '$ENV_FILE'
        fi
      done < '$tmp_env'
    "
  fi
  rm -f "$tmp_env"
  run chmod 0644 "$ENV_FILE"
  run chown root:root "$ENV_FILE"
}

install_wrapper_bin() {
  log "install /usr/local/bin/smolotchi wrapper pinned to /opt venv"
  local wrapper="/usr/local/bin/smolotchi"
  if [[ "$APPLY" -eq 1 ]]; then
    cat >"$wrapper" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

# Always run from the canonical /opt deploy venv.
VENV="/opt/smolotchi/current/.venv"
exec "${VENV}/bin/python" -m smolotchi.cli "$@"
EOF
    chmod 0755 "$wrapper"
    chown root:root "$wrapper"
  else
    log "PREVIEW: write wrapper to /usr/local/bin/smolotchi"
  fi
}

install_systemd_units_and_dropins() {
  log "install systemd units + dropins"

  # Units
  for u in "${UNITS[@]}"; do
    run install -m 0644 "$DEPLOY_DIR/packaging/systemd/$u" "$SYSTEMD_DIR/$u"
  done
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    run install -m 0644 "$DEPLOY_DIR/packaging/systemd/$DISPLAY_UNIT" "$SYSTEMD_DIR/$DISPLAY_UNIT"
  fi

  # Drop-in dirs
  local unit
  for unit in smolotchi-core smolotchi-core-net smolotchi-web smolotchi-ai smolotchi-prune; do
    run install -d -m 0755 "${SYSTEMD_DIR}/${unit}.service.d"
  done
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    run install -d -m 0755 "${SYSTEMD_DIR}/smolotchi-display.service.d"
  fi

  # IMPORTANT: ExecStart override to venv python in /opt (05-venv-execstart.conf)
  # This prevents drifting to any home install.
  local mk_execstart_dropin
  mk_execstart_dropin() {
    local svc="$1"  # e.g. smolotchi-core.service
    local cmd="$2"  # e.g. core
    local d="${SYSTEMD_DIR}/${svc}.d"
    if [[ "$APPLY" -eq 1 ]]; then
      cat >"${d}/05-venv-execstart.conf" <<EOF
[Service]
ExecStart=
ExecStart=/opt/smolotchi/current/.venv/bin/python -m smolotchi.cli ${cmd}
EOF
      chmod 0644 "${d}/05-venv-execstart.conf"
    else
      log "PREVIEW: write ${d}/05-venv-execstart.conf (cmd=${cmd})"
    fi
  }

  mk_execstart_dropin "smolotchi-core.service" "core"
  mk_execstart_dropin "smolotchi-core-net.service" "core"
  mk_execstart_dropin "smolotchi-web.service" "web"
  mk_execstart_dropin "smolotchi-ai.service" "ai"
  mk_execstart_dropin "smolotchi-prune.service" "prune"
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    mk_execstart_dropin "smolotchi-display.service" "display"
  fi

  # Copy packaged hardening dropins
  # (baseline + per-unit dirs already in repo)
  run bash -lc "install -m 0644 '$DEPLOY_DIR/packaging/systemd/dropins/'*.conf '$SYSTEMD_DIR/smolotchi-core.service.d/'"
  run bash -lc "install -m 0644 '$DEPLOY_DIR/packaging/systemd/dropins/'*.conf '$SYSTEMD_DIR/smolotchi-core-net.service.d/'"
  run bash -lc "install -m 0644 '$DEPLOY_DIR/packaging/systemd/dropins/'*.conf '$SYSTEMD_DIR/smolotchi-web.service.d/'"
  run bash -lc "install -m 0644 '$DEPLOY_DIR/packaging/systemd/dropins/'*.conf '$SYSTEMD_DIR/smolotchi-ai.service.d/'"
  run bash -lc "install -m 0644 '$DEPLOY_DIR/packaging/systemd/dropins/'*.conf '$SYSTEMD_DIR/smolotchi-prune.service.d/'"
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    run bash -lc "install -m 0644 '$DEPLOY_DIR/packaging/systemd/dropins/'*.conf '$SYSTEMD_DIR/smolotchi-display.service.d/'"
  fi

  # Per-unit dropin dirs (if present)
  run bash -lc "if compgen -G '$DEPLOY_DIR/packaging/systemd/dropins/smolotchi-core.service.d/*.conf' >/dev/null; then install -m 0644 $DEPLOY_DIR/packaging/systemd/dropins/smolotchi-core.service.d/*.conf '$SYSTEMD_DIR/smolotchi-core.service.d/'; fi"
  run bash -lc "if compgen -G '$DEPLOY_DIR/packaging/systemd/dropins/smolotchi-core-net.service.d/*.conf' >/dev/null; then install -m 0644 $DEPLOY_DIR/packaging/systemd/dropins/smolotchi-core-net.service.d/*.conf '$SYSTEMD_DIR/smolotchi-core-net.service.d/'; fi"
  run bash -lc "if compgen -G '$DEPLOY_DIR/packaging/systemd/dropins/smolotchi-web.service.d/*.conf' >/dev/null; then install -m 0644 $DEPLOY_DIR/packaging/systemd/dropins/smolotchi-web.service.d/*.conf '$SYSTEMD_DIR/smolotchi-web.service.d/'; fi"
  run bash -lc "if compgen -G '$DEPLOY_DIR/packaging/systemd/dropins/smolotchi-ai.service.d/*.conf' >/dev/null; then install -m 0644 $DEPLOY_DIR/packaging/systemd/dropins/smolotchi-ai.service.d/*.conf '$SYSTEMD_DIR/smolotchi-ai.service.d/'; fi"
  run bash -lc "if compgen -G '$DEPLOY_DIR/packaging/systemd/dropins/smolotchi-prune.service.d/*.conf' >/dev/null; then install -m 0644 $DEPLOY_DIR/packaging/systemd/dropins/smolotchi-prune.service.d/*.conf '$SYSTEMD_DIR/smolotchi-prune.service.d/'; fi"
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    run bash -lc "if compgen -G '$DEPLOY_DIR/packaging/systemd/dropins/smolotchi-display.service.d/*.conf' >/dev/null; then install -m 0644 $DEPLOY_DIR/packaging/systemd/dropins/smolotchi-display.service.d/*.conf '$SYSTEMD_DIR/smolotchi-display.service.d/'; fi"
  fi

  # tmpfiles
  run install -d -m 0755 "$TMPFILES_DIR"
  run install -m 0644 "$DEPLOY_DIR/packaging/systemd/tmpfiles.d/smolotchi.conf" "$TMPFILES_FILE"
  run systemd-tmpfiles --create "$TMPFILES_FILE" || true

  run systemctl daemon-reload
}

enable_services() {
  log "enable/start services"
  run systemctl enable --now smolotchi-prune.timer

  run systemctl enable --now smolotchi-ai.service
  run systemctl enable --now smolotchi-web.service

  if [[ "$ENABLE_CORE_NET" -eq 1 ]]; then
    run systemctl disable --now smolotchi-core.service || true
    run systemctl enable --now smolotchi-core-net.service
  else
    run systemctl disable --now smolotchi-core-net.service || true
    run systemctl enable --now smolotchi-core.service
  fi

  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    run systemctl enable --now smolotchi-display.service
  fi
}

post_checks() {
  log "post-check hints"
  cat <<EOF
Mode: $MODE

Check:
  systemctl status smolotchi-core smolotchi-web smolotchi-ai --no-pager
  journalctl -u smolotchi-core -n 50 --no-pager

Verify install is pinned to /opt:
  /opt/smolotchi/current/.venv/bin/python -c "import smolotchi; import smolotchi.cli as c; print('smolotchi:', getattr(smolotchi,'__file__',None)); print('cli:', c.__file__)"

If you used PREVIEW, rerun with:
  sudo $0 --apply [same flags...]
EOF
}

main() {
  log "Mode: $MODE"
  ensure_apt
  ensure_user
  ensure_dirs

  local project_dir
  project_dir="$(detect_project_dir || true)"
  checkout_or_update_repo "$project_dir"

  # If running inside repo, still deploy it into /opt so runtime is canonical
  if [[ -n "$project_dir" ]]; then
    log "Sync local repo -> /opt deploy dir"
    run rsync -a --delete --exclude '.git' "$project_dir/" "$DEPLOY_DIR/"
  fi

  install_venv_and_package
  install_config_and_env
  install_wrapper_bin
  install_systemd_units_and_dropins
  enable_services
  post_checks
}

main "$@"
