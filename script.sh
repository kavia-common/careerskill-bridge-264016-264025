#!/usr/bin/env bash
# SkillBridge backend runner (manual local run)
#
# This script is intended for *manual* development runs. It does NOT change any
# PreviewManager/CI configuration.
#
# Features:
# - Safe bash: set -euo pipefail
# - Installs backend Python dependencies idempotently (skips when already present, unless forced)
# - Runs backend (FastAPI) on a configurable port (default: 3001)
# - Gracefully handles the common case where port 3001 is already in use (often by PreviewManager)
# - Clean shutdown (SIGINT/SIGTERM trap)
#
# Usage:
#   chmod +x ./script.sh
#   ./script.sh
#
# Optional environment variables:
#   INSTALL_DEPS=1        Install missing deps if not installed (default: 1)
#   FORCE_INSTALL=1       Force reinstall deps even if they look installed (default: 0)
#   BACKEND_PORT=3001     Backend port override (default: 3001)
#                         Special: BACKEND_PORT=0 auto-selects a free ephemeral port.
#   BACKEND_HOST=0.0.0.0  Backend bind host (default: 0.0.0.0)
#
# Notes:
# - Backend reads config from a .env file at repo root or backend/ (Pydantic settings).
# - This script deliberately does NOT install/run the frontend.
# - This script will NOT stop/kill any existing process using a port; it will only detect and guide.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"

INSTALL_DEPS="${INSTALL_DEPS:-1}"
FORCE_INSTALL="${FORCE_INSTALL:-0}"

BACKEND_PORT="${BACKEND_PORT:-3001}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"

# ----------------------------
# Logging helpers
# ----------------------------
timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  local scope="$1"
  shift
  echo "[$(timestamp)] [${scope}] $*"
}

# Run a command and prefix every output line with a scope label.
# stdout+stderr are combined to preserve ordering.
run_prefixed() {
  local scope="$1"
  shift
  # Using stdbuf when available makes prefixing more "real time".
  if command -v stdbuf >/dev/null 2>&1; then
    stdbuf -oL -eL "$@" 2>&1 | sed -u "s/^/[$(timestamp)] [${scope}] /"
  else
    "$@" 2>&1 | sed -u "s/^/[$(timestamp)] [${scope}] /"
  fi
}

# ----------------------------
# Validation
# ----------------------------
if [[ ! -d "${BACKEND_DIR}" ]]; then
  log "runner" "ERROR: backend directory not found at: ${BACKEND_DIR}"
  exit 1
fi

# ----------------------------
# Port selection / preflight
# ----------------------------
is_port_listening() {
  local port="$1"
  # ss is widely available in Linux images; prefer it for speed/stability.
  # We only check LISTEN sockets because that's what prevents binding.
  if command -v ss >/dev/null 2>&1; then
    ss -ltn "sport = :${port}" 2>/dev/null | awk 'NR>1 {found=1} END {exit(found?0:1)}'
    return $?
  fi

  # Fallbacks for unusual environments.
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
    return $?
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -n tcp "${port}" >/dev/null 2>&1
    return $?
  fi

  # Last-resort: assume not listening if we cannot detect.
  return 1
}

port_owner_hint() {
  local port="$1"
  # Best-effort hint only; never fail the script if these tools aren't present.
  if command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"${port}" -sTCP:LISTEN 2>/dev/null | awk 'NR==2 {print $1" (pid "$2")"}'
    return 0
  fi
  if command -v ss >/dev/null 2>&1; then
    # Extract pid=... when possible
    ss -ltnp "sport = :${port}" 2>/dev/null | awk 'NR==2 {print $NF}' | sed 's/users:(("//; s/")).*$//'
    return 0
  fi
  echo ""
}

choose_free_port() {
  # Bind to port 0 on localhost to let the OS pick a free port, then close immediately.
  # This is deterministic and avoids racy "pick a random port" logic.
  python - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(("127.0.0.1", 0))
port = s.getsockname()[1]
s.close()
print(port)
PY
}

validate_and_select_port() {
  local requested_port="$1"

  if [[ "${requested_port}" == "0" ]]; then
    local selected
    selected="$(choose_free_port)"
    log "runner" "BACKEND_PORT=0 requested; selected free port: ${selected}"
    echo "${selected}"
    return 0
  fi

  if ! [[ "${requested_port}" =~ ^[0-9]+$ ]] || ((requested_port < 1 || requested_port > 65535)); then
    log "runner" "ERROR: BACKEND_PORT must be an integer in range 1..65535 (or 0 for auto). Got: ${requested_port}"
    exit 1
  fi

  if is_port_listening "${requested_port}"; then
    local hint
    hint="$(port_owner_hint "${requested_port}")"
    log "runner" "ERROR: Port ${requested_port} is already in use (a process is listening)."
    if [[ -n "${hint}" ]]; then
      log "runner" "Hint: listener appears to be: ${hint}"
    fi
    log "runner" "Common cause: the Preview system is already running the backend on port ${requested_port}."
    log "runner" "Action options:"
    log "runner" "  1) Use the already-running backend (recommended when preview is active):"
    log "runner" "     - Open docs at: http://localhost:${requested_port}/docs"
    log "runner" "  2) Run this script on a different port:"
    log "runner" "     - BACKEND_PORT=3002 ./script.sh"
    log "runner" "  3) Let this script auto-select a free port:"
    log "runner" "     - BACKEND_PORT=0 ./script.sh"
    exit 2
  fi

  echo "${requested_port}"
}

BACKEND_PORT="$(validate_and_select_port "${BACKEND_PORT}")"

# ----------------------------
# Dependency installation (idempotent)
# ----------------------------
install_backend_deps_if_needed() {
  if [[ ! -f "${BACKEND_DIR}/requirements.txt" ]]; then
    log "backend" "ERROR: requirements.txt not found in ${BACKEND_DIR}"
    exit 1
  fi

  # Heuristic: if uvicorn+fastapi import works, deps likely installed in current interpreter env.
  if [[ "${FORCE_INSTALL}" == "1" ]]; then
    log "backend" "FORCE_INSTALL=1 set; reinstalling Python dependencies..."
  else
    if python -c "import uvicorn, fastapi" >/dev/null 2>&1; then
      log "backend" "Python deps look installed (import uvicorn/fastapi succeeded); skipping install."
      return
    fi
  fi

  log "backend" "Installing Python dependencies (pip)..."
  (
    cd "${BACKEND_DIR}"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
  )
  log "backend" "Python dependencies installed."
}

if [[ "${INSTALL_DEPS}" == "1" ]]; then
  install_backend_deps_if_needed
else
  log "runner" "INSTALL_DEPS=0 set; skipping dependency installation."
fi

# ----------------------------
# Process management
# ----------------------------
BACKEND_PID=""

cleanup() {
  # Make this safe to call multiple times
  set +e

  log "runner" "Shutting down..."

  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    log "runner" "Stopping backend (pid ${BACKEND_PID})..."
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi

  # Give process a moment to exit gracefully
  sleep 1

  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    log "runner" "Backend did not stop gracefully; sending SIGKILL..."
    kill -9 "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi

  log "runner" "Shutdown complete."
}

trap cleanup SIGINT SIGTERM

start_backend() {
  log "backend" "Starting FastAPI on ${BACKEND_HOST}:${BACKEND_PORT} ..."
  (
    cd "${BACKEND_DIR}"
    # Enforce expected ports for manual run, unless caller overrides via BACKEND_PORT/BACKEND_HOST.
    export PORT="${BACKEND_PORT}"
    export HOST="${BACKEND_HOST}"
    # Run backend using its provided entrypoint (uvicorn defaults inside).
    run_prefixed "backend" python -m src.api.serve
  ) &
  BACKEND_PID="$!"
  log "backend" "Started (pid ${BACKEND_PID})."
}

log "runner" "Launching backend..."
start_backend

log "runner" "Backend running:"
log "runner" " - Backend: http://localhost:${BACKEND_PORT} (docs: http://localhost:${BACKEND_PORT}/docs)"
log "runner" "Press Ctrl+C to stop."

# Wait until backend exits, then cleanup.
wait "${BACKEND_PID}" || true
cleanup
exit 0
