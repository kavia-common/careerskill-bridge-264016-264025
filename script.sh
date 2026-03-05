#!/usr/bin/env bash
# SkillBridge full-stack runner (manual local run)
#
# This script is intended for *manual* development runs. It does NOT change any
# PreviewManager/CI configuration.
#
# Features:
# - Safe bash: set -euo pipefail
# - Idempotent dependency installs (skips when already present, unless forced)
# - Runs backend (FastAPI) on port 3001 and frontend (React) on port 3000
# - Runs both processes concurrently with clean shutdown (SIGINT/SIGTERM trap)
# - Clear, prefixed logs for each service
#
# Usage:
#   ./script.sh
#
# Optional environment variables:
#   INSTALL_DEPS=1            Install missing deps if not installed (default: 1)
#   FORCE_INSTALL=1           Force reinstall deps even if they look installed (default: 0)
#   FRONTEND_PORT=3000        Frontend port override (default: 3000)
#   BACKEND_PORT=3001         Backend port override (default: 3001)
#   FRONTEND_HOST=0.0.0.0     Frontend bind host (default: 0.0.0.0)
#   BACKEND_HOST=0.0.0.0      Backend bind host (default: 0.0.0.0)
#
# Notes:
# - Backend reads config from a .env file at repo root or backend/ (Pydantic settings).
# - Frontend reads REACT_APP_* variables at build/start time (.env in frontend folder or env).
# - For local dev, you typically want:
#     REACT_APP_API_BASE=http://localhost:3001
#     REACT_APP_WS_URL=ws://localhost:3001/ws/notifications

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_DIR="${SCRIPT_DIR}/backend"
# Frontend is in a sibling workspace (separate container workspace in this repo layout).
FRONTEND_DIR="${SCRIPT_DIR}/../careerskill-bridge-264016-264026/frontend_web_app"

INSTALL_DEPS="${INSTALL_DEPS:-1}"
FORCE_INSTALL="${FORCE_INSTALL:-0}"

FRONTEND_PORT="${FRONTEND_PORT:-3000}"
BACKEND_PORT="${BACKEND_PORT:-3001}"

FRONTEND_HOST="${FRONTEND_HOST:-0.0.0.0}"
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

if [[ ! -d "${FRONTEND_DIR}" ]]; then
  log "runner" "ERROR: frontend directory not found at: ${FRONTEND_DIR}"
  log "runner" "Expected path: ${FRONTEND_DIR}"
  exit 1
fi

if [[ "${FRONTEND_PORT}" == "${BACKEND_PORT}" ]]; then
  log "runner" "ERROR: FRONTEND_PORT and BACKEND_PORT must be different (both are ${FRONTEND_PORT})"
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

  # Heuristic: if uvicorn import works, deps probably installed.
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

install_frontend_deps_if_needed() {
  if [[ ! -f "${FRONTEND_DIR}/package.json" ]]; then
    log "frontend" "ERROR: package.json not found in ${FRONTEND_DIR}"
    exit 1
  fi

  # Heuristic: node_modules existence usually indicates install done.
  if [[ "${FORCE_INSTALL}" == "1" ]]; then
    log "frontend" "FORCE_INSTALL=1 set; reinstalling Node dependencies..."
  else
    if [[ -d "${FRONTEND_DIR}/node_modules" ]]; then
      log "frontend" "node_modules exists; skipping npm install."
      return
    fi
  fi

  log "frontend" "Installing Node dependencies (npm ci if lockfile exists, else npm install)..."
  (
    cd "${FRONTEND_DIR}"
    if [[ -f "package-lock.json" ]]; then
      npm ci
    else
      npm install
    fi
  )
  log "frontend" "Node dependencies installed."
}

if [[ "${INSTALL_DEPS}" == "1" ]]; then
  install_backend_deps_if_needed
  install_frontend_deps_if_needed
else
  log "runner" "INSTALL_DEPS=0 set; skipping dependency installation."
fi

# ----------------------------
# Process management
# ----------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  # Make this safe to call multiple times
  set +e

  log "runner" "Shutting down..."

  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" >/dev/null 2>&1; then
    log "runner" "Stopping frontend (pid ${FRONTEND_PID})..."
    kill "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi

  if [[ -n "${BACKEND_PID}" ]] && kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
    log "runner" "Stopping backend (pid ${BACKEND_PID})..."
    kill "${BACKEND_PID}" >/dev/null 2>&1 || true
  fi

  # Give processes a moment to exit gracefully
  sleep 1

  if [[ -n "${FRONTEND_PID}" ]] && kill -0 "${FRONTEND_PID}" >/dev/null 2>&1; then
    log "runner" "Frontend did not stop gracefully; sending SIGKILL..."
    kill -9 "${FRONTEND_PID}" >/dev/null 2>&1 || true
  fi

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

start_frontend() {
  log "frontend" "Starting React dev server on ${FRONTEND_HOST}:${FRONTEND_PORT} ..."
  (
    cd "${FRONTEND_DIR}"
    # CRA uses PORT; HOST is also respected.
    export PORT="${FRONTEND_PORT}"
    export HOST="${FRONTEND_HOST}"
    # Avoid opening browser automatically in some environments.
    export BROWSER="${BROWSER:-none}"
    run_prefixed "frontend" npm start
  ) &
  FRONTEND_PID="$!"
  log "frontend" "Started (pid ${FRONTEND_PID})."
}

log "runner" "Launching services..."
start_backend
start_frontend

log "runner" "Services running:"
log "runner" " - Backend:  http://localhost:${BACKEND_PORT}   (docs: /docs)"
log "runner" " - Frontend: http://localhost:${FRONTEND_PORT}"
log "runner" "Press Ctrl+C to stop."

# Wait until either process exits; then stop the other.
# bash 4.3+ has wait -n; provide a portable fallback.
if wait -n "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null; then
  log "runner" "A service exited; shutting down the other..."
else
  # Fallback for shells without wait -n: poll.
  while true; do
    if ! kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
      log "runner" "Backend exited; shutting down..."
      break
    fi
    if ! kill -0 "${FRONTEND_PID}" >/dev/null 2>&1; then
      log "runner" "Frontend exited; shutting down..."
      break
    fi
    sleep 1
  done
fi

cleanup
exit 0
