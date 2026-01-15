#!/usr/bin/env bash
set -euo pipefail

# Smolotchi canonical bootstrap + deploy (Pi)
# - root-only
# - deploy checkout to:      /opt/smolotchi/current
# - venv lives in:           /opt/smolotchi/current/.venv
# - config/env live in:      /etc/smolotchi/{config.toml,env}
# - state/runtime live in:   /var/lib/smolotchi + /run/smolotchi
#
# Usage (curl|bash):
#   curl -sfL https://raw.githubusercontent.com/161sam/smolotchi/main/scripts/deploy.sh | sudo bash -s -- \
#     --repo https://github.com/161sam/smolotchi.git --branch main --apply
#
# Usage (local repo):
#   sudo ./scripts/deploy.sh --apply
#
# Flags:
#   --repo <git-url>      (optional if running inside repo; required for curl|bash)
#   --branch <name>       (default: main)
#   --root <path>         (default: /opt/smolotchi/current)
#   --user <name>         (default: smolotchi)
#   --with-display        (install+enable display service)
#   --enable-core-net     (enables smolotchi-core-net and disables smolotchi-core)
#   --skip-apt            (skip apt install step)
#   --apply               (actually perform changes; default is PREVIEW)
#   --force               (ignore some safety checks)
#   -h|--help

REPO_URL=""
BRANCH="main"
USER_NAME="smolotchi"
WITH_DISPLAY=0
ENABLE_CORE_NET=0
SKIP_APT=0
APPLY=0
FORCE=0
DEPLOY_DIR="/opt/smolotchi/current"

MODE="PREVIEW"

log() { echo "[deploy] $*"; }
die() { echo "[deploy] ERROR: $*" >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO_URL="$2"; shift 2;;
    --branch) BRANCH="$2"; shift 2;;
    --root) DEPLOY_DIR="$2"; shift 2;;
    --user) USER_NAME="$2"; shift 2;;
    --with-display) WITH_DISPLAY=1; shift;;
    --enable-core-net) ENABLE_CORE_NET=1; shift;;
    --skip-apt) SKIP_APT=1; shift;;
    --apply) APPLY=1; MODE="APPLY"; shift;;
    --force) FORCE=1; shift;;
    -h|--help)
      sed -n '1,120p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) die "Unknown arg: $1";;
  esac
done

[[ $EUID -eq 0 ]] || die "run as root (sudo)."

VENV_DIR="${DEPLOY_DIR}/.venv"
ETC_DIR="/etc/smolotchi"
ENV_FILE="${ETC_DIR}/env"
CFG_FILE="${ETC_DIR}/config.toml"

SYSTEMD_DIR="/etc/systemd/system"
TMPFILES_DIR="/etc/tmpfiles.d"

# Units expected in repo under packaging/systemd
UNITS=(
  "smolotchi-core.service"
  "smolotchi-core-net.service"
  "smolotchi-web.service"
  "smolotchi-ai.service"
  "smolotchi-prune.service"
  "smolotchi-prune.timer"
)
DISPLAY_UNIT="smolotchi-display.service"

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
    git ca-certificates curl \
    python3 python3-venv python3-pip \
    sqlite3 \
    iw wireless-tools rfkill iproute2 \
    systemd procps

  # optional tools best-effort
  run bash -lc 'apt-get install -y --no-install-recommends jq nmap tcpdump || true'
}

ensure_user() {
  log "ensure user: ${USER_NAME}"
  if ! id "$USER_NAME" >/dev/null 2>&1; then
    run useradd -m -s /bin/bash "$USER_NAME"
  fi
}

ensure_dirs() {
  log "ensure dirs (/var/lib, /run, /etc, /opt)"
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /var/lib/smolotchi/artifacts
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi
  run install -d -m 0775 -o "$USER_NAME" -g "$USER_NAME" /run/smolotchi/locks
  run install -d -m 0755 "$ETC_DIR"
  run install -d -m 0755 "$DEPLOY_DIR"
}

detect_project_dir() {
  # If running inside repo: PROJECT_DIR is repo root (contains pyproject.toml)
  if [[ -f "./pyproject.toml" && -d "./smolotchi" && -d "./packaging" ]]; then
    echo "$(pwd)"
    return
  fi
  echo ""
}

checkout_or_update_repo() {
  local project_dir="$1"

  # local repo mode
  if [[ -n "$project_dir" && -z "$REPO_URL" ]]; then
    log "Using local repo at: $project_dir"
    require_cmd rsync
    run rsync -a --delete \
      --exclude '.git' \
      --exclude '.venv' \
      --exclude 'node_modules' \
      "$project_dir/" "$DEPLOY_DIR/"
    return 0
  fi

  # curl|bash mode
  if [[ -z "$REPO_URL" ]]; then
    die "not running inside repo and --repo not provided (required for curl|bash)."
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
  run "$VENV_DIR/bin/pip" install -r "$DEPLOY_DIR/requirements/base.txt" -r "$DEPLOY_DIR/requirements/pi_zero.txt"
  run "$VENV_DIR/bin/pip" install -e "$DEPLOY_DIR"
}

install_config_and_env() {
  log "install /etc/smolotchi/config.toml + env"

  # config.toml: copy from repo if missing
  if [[ ! -f "$CFG_FILE" ]]; then
    run install -m 0644 "$DEPLOY_DIR/config.toml" "$CFG_FILE"
    run chown root:root "$CFG_FILE"
  else
    log "config exists: $CFG_FILE (keeping)"
  fi

  # env: enforce SMOLOTCHI_CONFIG -> /etc/smolotchi/config.toml (ProtectHome-safe)
  local tmp_env
  tmp_env="$(mktemp)"
  cat >"$tmp_env" <<EOF
SMOLOTCHI_DB=/var/lib/smolotchi/events.db
SMOLOTCHI_ARTIFACT_ROOT=/var/lib/smolotchi/artifacts
SMOLOTCHI_CONFIG=/etc/smolotchi/config.toml
SMOLOTCHI_DEVICE=pi_zero
SMOLOTCHI_LOCK_ROOT=/run/smolotchi/locks
EOF

  if [[ ! -f "$ENV_FILE" ]]; then
    run install -m 0644 "$tmp_env" "$ENV_FILE"
  else
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
  log "install /usr/local/bin/smolotchi wrapper pinned to deploy venv"
  local wrapper="/usr/local/bin/smolotchi"
  if [[ "$APPLY" -eq 1 ]]; then
    cat >"$wrapper" <<EOF
#!/usr/bin/env bash
set -euo pipefail
exec "${VENV_DIR}/bin/python" -m smolotchi.cli "\$@"
EOF
    chmod 0755 "$wrapper"
    chown root:root "$wrapper"
  else
    log "PREVIEW: write wrapper to ${wrapper}"
  fi
}

install_unit_file() {
  local unit="$1"
  local src="$DEPLOY_DIR/packaging/systemd/$unit"
  local dst="$SYSTEMD_DIR/$unit"
  [[ -f "$src" ]] || die "missing unit file: $src"
  run install -m 0644 "$src" "$dst"
}

ensure_dropin_dir() {
  local unit="$1"  # e.g. smolotchi-core.service
  run install -d -m 0755 "${SYSTEMD_DIR}/${unit}.d"
}

write_execstart_dropin() {
  local unit="$1"     # e.g. smolotchi-core.service
  local cmd="$2"      # e.g. core / web / ai / prune / display
  local d="${SYSTEMD_DIR}/${unit}.d"
  local f="${d}/05-venv-execstart.conf"

  if [[ "$APPLY" -eq 1 ]]; then
    cat >"$f" <<EOF
[Service]
ExecStart=
ExecStart=${VENV_DIR}/bin/python -m smolotchi.cli ${cmd}
EOF
    chmod 0644 "$f"
    chown root:root "$f"
  else
    log "PREVIEW: write ${f} (cmd=${cmd})"
  fi
}

copy_if_exists() {
  local src="$1"
  local dst_dir="$2"
  if [[ -f "$src" ]]; then
    run install -m 0644 "$src" "$dst_dir/"
  else
    log "skip (missing): $src"
  fi
}

install_baseline_dropins_for_unit() {
  local unit="$1"  # e.g. smolotchi-core.service
  local d="${SYSTEMD_DIR}/${unit}.d"

  # Baseline dropins are in packaging/systemd/dropins/*.conf
  local dropins_root="$DEPLOY_DIR/packaging/systemd/dropins"

  # --- Whitelist per unit (SAFE)
  case "$unit" in
    smolotchi-core.service|smolotchi-core-net.service)
      copy_if_exists "$dropins_root/10-hardening.conf" "$d"
      copy_if_exists "$dropins_root/11-protect-home.conf" "$d"
      copy_if_exists "$dropins_root/12-restart-protection.conf" "$d"
      copy_if_exists "$dropins_root/15-runtime-dirs.conf" "$d"
      copy_if_exists "$dropins_root/40-notify.conf" "$d"
      ;;
    smolotchi-web.service)
      copy_if_exists "$dropins_root/10-hardening.conf" "$d"
      copy_if_exists "$dropins_root/11-protect-home.conf" "$d"
      copy_if_exists "$dropins_root/12-restart-protection.conf" "$d"
      copy_if_exists "$dropins_root/15-runtime-dirs.conf" "$d"
      copy_if_exists "$dropins_root/20-cap-defaults.conf" "$d"
      ;;
    smolotchi-ai.service)
      copy_if_exists "$dropins_root/10-hardening.conf" "$d"
      copy_if_exists "$dropins_root/11-protect-home.conf" "$d"
      copy_if_exists "$dropins_root/12-restart-protection.conf" "$d"
      copy_if_exists "$dropins_root/15-runtime-dirs.conf" "$d"
      ;;
    smolotchi-prune.service)
      # prune has its own hardening dropin in your tree
      copy_if_exists "$dropins_root/10-hardening-prune.conf" "$d"
      copy_if_exists "$dropins_root/12-restart-protection.conf" "$d"
      copy_if_exists "$dropins_root/15-runtime-dirs.conf" "$d"
      ;;
    smolotchi-display.service)
      copy_if_exists "$dropins_root/10-hardening.conf" "$d"
      copy_if_exists "$dropins_root/11-protect-home.conf" "$d"
      copy_if_exists "$dropins_root/12-restart-protection.conf" "$d"
      copy_if_exists "$dropins_root/15-runtime-dirs.conf" "$d"
      ;;
    *)
      die "unknown unit for baseline dropins: $unit"
      ;;
  esac
}

install_per_unit_dropins() {
  local unit="$1"
  local d="${SYSTEMD_DIR}/${unit}.d"
  local src_dir="$DEPLOY_DIR/packaging/systemd/dropins/${unit}.d"
  if compgen -G "${src_dir}/*.conf" >/dev/null 2>&1; then
    run install -m 0644 "${src_dir}"/*.conf "$d/"
  fi
}

install_tmpfiles() {
  local src="$DEPLOY_DIR/packaging/systemd/tmpfiles.d/smolotchi.conf"
  [[ -f "$src" ]] || die "missing tmpfiles: $src"
  run install -d -m 0755 "$TMPFILES_DIR"
  run install -m 0644 "$src" "$TMPFILES_DIR/smolotchi.conf"
  run systemd-tmpfiles --create "$TMPFILES_DIR/smolotchi.conf" || true
}

install_systemd_all() {
  log "install systemd units + dropins (whitelist)"
  # units
  for u in "${UNITS[@]}"; do
    install_unit_file "$u"
    ensure_dropin_dir "$u"
  done
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    install_unit_file "$DISPLAY_UNIT"
    ensure_dropin_dir "$DISPLAY_UNIT"
  fi

  # execstart pinned dropins
  write_execstart_dropin "smolotchi-core.service" "core"
  write_execstart_dropin "smolotchi-core-net.service" "core"
  write_execstart_dropin "smolotchi-web.service" "web"
  write_execstart_dropin "smolotchi-ai.service" "ai"
  write_execstart_dropin "smolotchi-prune.service" "prune"
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    write_execstart_dropin "smolotchi-display.service" "display"
  fi

  # baseline dropins (whitelist) + per-unit dropins
  install_baseline_dropins_for_unit "smolotchi-core.service"
  install_per_unit_dropins "smolotchi-core.service"

  install_baseline_dropins_for_unit "smolotchi-core-net.service"
  install_per_unit_dropins "smolotchi-core-net.service"

  install_baseline_dropins_for_unit "smolotchi-web.service"
  install_per_unit_dropins "smolotchi-web.service"

  install_baseline_dropins_for_unit "smolotchi-ai.service"
  install_per_unit_dropins "smolotchi-ai.service"

  install_baseline_dropins_for_unit "smolotchi-prune.service"
  install_per_unit_dropins "smolotchi-prune.service"

  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    install_baseline_dropins_for_unit "smolotchi-display.service"
    install_per_unit_dropins "smolotchi-display.service"
  fi

  install_tmpfiles

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

  # restart best-effort to apply changes
  run systemctl try-restart smolotchi-prune.timer || true
  run systemctl try-restart smolotchi-ai.service || true
  run systemctl try-restart smolotchi-web.service || true
  run systemctl try-restart smolotchi-core.service || true
  run systemctl try-restart smolotchi-core-net.service || true
  if [[ "$WITH_DISPLAY" -eq 1 ]]; then
    run systemctl try-restart smolotchi-display.service || true
  fi
}

post_checks() {
  log "post-check hints"
  cat <<EOF
Mode: $MODE

Check:
  systemctl --no-pager --full status smolotchi-core smolotchi-web smolotchi-ai | sed -n '1,140p'
  journalctl -u smolotchi-core -n 60 --no-pager

Verify install pinned to deploy root:
  ${VENV_DIR}/bin/pip show -f smolotchi | sed -n '1,120p'
  ${VENV_DIR}/bin/python -c "import smolotchi, smolotchi.cli as c; print('pkg:', getattr(smolotchi,'__file__',None)); print('cli:', c.__file__)"

If PREVIEW was used, re-run with:
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

  install_venv_and_package
  install_config_and_env
  install_wrapper_bin
  install_systemd_all
  enable_services
  post_checks
}

main "$@"
