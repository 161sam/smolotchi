#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
    PYTHON_BIN="${REPO_ROOT}/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

SMO_SMOKE_URL="${SMO_SMOKE_URL:-http://127.0.0.1:8080}"
SMO_SMOKE_SCOPE="${SMO_SMOKE_SCOPE:-10.0.10.0/24}"
SMO_SMOKE_TIMEOUT_S="${SMO_SMOKE_TIMEOUT_S:-30}"
SMO_SMOKE_POLL_S="${SMO_SMOKE_POLL_S:-1}"
SMO_SMOKE_START_SERVICES="${SMO_SMOKE_START_SERVICES:-1}"
SMO_SMOKE_NOTE="${SMO_SMOKE_NOTE:-smoke-$(date +%s)}"

WEB_PID=""
WORKER_PID=""

cleanup() {
  if [[ -n "$WEB_PID" ]]; then
    kill "$WEB_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "$WORKER_PID" ]]; then
    kill "$WORKER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "$SMO_SMOKE_START_SERVICES" == "1" ]]; then
  echo "Starting web + worker..."
  (cd "$REPO_ROOT" && "$PYTHON_BIN" -m smolotchi.api.web) >/tmp/smolotchi-web.log 2>&1 &
  WEB_PID=$!
  (cd "$REPO_ROOT" && "$PYTHON_BIN" -m smolotchi.ai.worker --loop --log-level INFO) \
    >/tmp/smolotchi-ai-worker.log 2>&1 &
  WORKER_PID=$!
fi

printf "Waiting for web at %s" "$SMO_SMOKE_URL"
start_ts=$(date +%s)
while true; do
  if curl -fsS "$SMO_SMOKE_URL/" >/dev/null; then
    echo " ok"
    break
  fi
  now_ts=$(date +%s)
  if (( now_ts - start_ts > SMO_SMOKE_TIMEOUT_S )); then
    echo
    echo "error: web did not become ready within ${SMO_SMOKE_TIMEOUT_S}s"
    exit 1
  fi
  printf "."
  sleep "$SMO_SMOKE_POLL_S"
done

baseline=$(
  "$PYTHON_BIN" - <<'PY'
from smolotchi.core.artifacts import ArtifactStore
store = ArtifactStore("/var/lib/smolotchi/artifacts")
counts = {}
for kind in ("ai_job_link", "ai_plan_run"):
    counts[kind] = len(store.list(limit=200, kind=kind))
print(f"{counts['ai_job_link']} {counts['ai_plan_run']}")
PY
)

base_job_links=$(echo "$baseline" | awk '{print $1}')
base_plan_runs=$(echo "$baseline" | awk '{print $2}')

curl -fsS -X POST \
  -d "scope=${SMO_SMOKE_SCOPE}" \
  -d "note=${SMO_SMOKE_NOTE}" \
  "$SMO_SMOKE_URL/ai/run" >/dev/null

echo "Triggered /ai/run with note=${SMO_SMOKE_NOTE}"

job_status=""
job_id=""
start_ts=$(date +%s)
while true; do
  read -r job_id job_status < <(
    SMO_SMOKE_NOTE="$SMO_SMOKE_NOTE" "$PYTHON_BIN" - <<'PY'
import os
from smolotchi.core.jobs import JobStore
note = os.environ.get("SMO_SMOKE_NOTE", "")
js = JobStore()
jobs = [j for j in js.list(limit=50) if j.kind == "ai_plan" and note in (j.note or "")]
if not jobs:
    print("", "")
else:
    job = jobs[0]
    print(job.id, job.status)
PY
  )

  if [[ -n "$job_status" && "$job_status" != "queued" ]]; then
    echo "Job ${job_id} status=${job_status}"
    break
  fi

  now_ts=$(date +%s)
  if (( now_ts - start_ts > SMO_SMOKE_TIMEOUT_S )); then
    echo "error: job did not leave queued within ${SMO_SMOKE_TIMEOUT_S}s"
    exit 1
  fi
  sleep "$SMO_SMOKE_POLL_S"
done

post_counts=$(
  "$PYTHON_BIN" - <<'PY'
from smolotchi.core.artifacts import ArtifactStore
store = ArtifactStore("/var/lib/smolotchi/artifacts")
counts = {}
for kind in ("ai_job_link", "ai_plan_run"):
    counts[kind] = len(store.list(limit=200, kind=kind))
print(f"{counts['ai_job_link']} {counts['ai_plan_run']}")
PY
)

post_job_links=$(echo "$post_counts" | awk '{print $1}')
post_plan_runs=$(echo "$post_counts" | awk '{print $2}')

if (( post_job_links <= base_job_links )); then
  echo "error: expected ai_job_link to increase (before=${base_job_links} after=${post_job_links})"
  exit 1
fi

if (( post_plan_runs <= base_plan_runs )); then
  echo "error: expected ai_plan_run to increase (before=${base_plan_runs} after=${post_plan_runs})"
  exit 1
fi

echo "Smoke test passed"
