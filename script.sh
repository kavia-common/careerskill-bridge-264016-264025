#!/usr/bin/env bash
# SkillBridge backend runner (manual local run)
#
# This script is intended for *manual* development runs. It does NOT change any
# PreviewManager/CI configuration.
#
# Features:
# - Safe bash: set -euo pipefail
# - Installs backend Python dependencies idempotently (skips when already present, unless forced)
# - Runs backend (FastAPI) on port 3001
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
#   BACKEND_HOST=0.0.0.0  Backend bind host (default: 0.0.0.0)
#
# Notes:
# - Backend reads config from a .env file at repo root or backend/ (Pydantic settings).
# - This script deliberately does NOT install/run the frontend.

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
