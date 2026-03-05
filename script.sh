#!/usr/bin/env bash
# SkillBridge backend runner (manual local run)
#
# This script is intended for *manual* development runs. It does NOT change any
# PreviewManager/CI configuration.
#
# Flow contract (BackendRunFlow):
# - Inputs (env vars):
#   - INSTALL_DEPS=1|0        Install missing deps if not installed (default: 1)
#   - FORCE_INSTALL=1|0       Force reinstall deps (default: 0)
#   - BACKEND_PORT=3001|0     Port override; 0 auto-selects a free port (default: 3001)
#   - BACKEND_HOST=0.0.0.0    Bind host (default: 0.0.0.0)
#   - STARTUP_TIMEOUT_SECONDS Startup readiness wait (default: 15)
# - Outputs:
#   - Exit 0: backend started and then stopped (Ctrl+C or process exit)
#   - Exit 2: requested port already in use (preflight)
#   - Exit 3: backend failed to become ready within timeout (startup failure)
# - Side effects:
#   - Optionally installs Python dependencies via pip
#   - Starts a backend process (FastAPI/uvicorn) and streams logs to stdout
# - Observability:
#   - All logs are timestamped with a scope prefix ([runner]/[backend])
#
# Usage:
#   chmod +x ./script.sh
#   ./script.sh
#
# Notes:
# - Backend reads config from a .env file at repo root or backend/ (Pydantic settings).
# - This script will NOT stop/kill any existing process using a port; it will only detect and guide.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"

INSTALL_DEPS="${INSTALL_DEPS:-1}"
FORCE_INSTALL="${FORCE_INSTALL:-0}"

BACKEND_PORT="${BACKEND_PORT:-3001}"
BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-15}"

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

if ! [[ "${STARTUP_TIMEOUT_SECONDS}" =~ ^[0-9]+$ ]] || ((STARTUP_TIMEOUT_SECONDS < 1 || STARTUP_TIMEOUT_SECONDS > 300)); then
  log "runner" "ERROR: STARTUP_TIMEOUT_SECONDS must be an integer in range 1..300. Got: ${STARTUP_TIMEOUT_SECONDS}"
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
    ss -ltnp "sport = :${port}" 2>/dev/null | awk 'NR==2 {print $NF}' | sed 's/users:((\"//; s/\")).*$//'
    return 0
  fi
  echo ""
}

choose_free_port() {
  # Bind to port 0 on localhost to let the OS pick a free port, then close immediately.
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
# Process management / readiness
# ----------------------------
BACKEND_PID=""
LOG_PIPE_PID=""

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

  if [[ -n "${LOG_PIPE_PID}" ]] && kill -0 "${LOG_PIPE_PID}" >/dev/null 2>&1; then
    kill "${LOG_PIPE_PID}" >/dev/null 2>&1 || true
  fi

  log "runner" "Shutdown complete."
}

on_sigint() {
  log "runner" "Received Ctrl+C (SIGINT)."
  cleanup
  exit 0
}

on_sigterm() {
  log "runner" "Received SIGTERM."
  cleanup
  exit 0
}

trap on_sigint SIGINT
trap on_sigterm SIGTERM

start_backend() {
  log "backend" "Starting FastAPI on ${BACKEND_HOST}:${BACKEND_PORT} ..."
  # Start backend and stream its logs with prefixing. Keep the uvicorn/python process PID.
  (
    cd "${BACKEND_DIR}"
    export PORT="${BACKEND_PORT}"
    export HOST="${BACKEND_HOST}"
    exec python -m src.api.serve
  ) 2>&1 | sed -u "s/^/[$(timestamp)] [backend] /" &
  LOG_PIPE_PID="$!"
  # The actual backend PID is not the pipe PID; capture it by starting in its own subshell.
  # To keep changes minimal and reliable, we use pgrep with a narrow match window.
  sleep 0.2
  BACKEND_PID="$(pgrep -n -f "python -m src.api.serve" || true)"

  if [[ -z "${BACKEND_PID}" ]]; then
    log "backend" "ERROR: failed to determine backend PID (process may have exited immediately)."
    return 1
  fi

  log "backend" "Started (pid ${BACKEND_PID})."
  return 0
}

http_ready_check() {
  # Prefer curl; fallback to python urllib.
  local url="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 1 "${url}" >/dev/null 2>&1
    return $?
  fi

  python - <<PY
import sys
import urllib.request
try:
    with urllib.request.urlopen("${url}", timeout=1) as r:
        # Any 2xx/3xx response indicates the server is up enough to answer.
        sys.exit(0)
except Exception:
    sys.exit(1)
PY
}

wait_for_backend_ready() {
  local timeout_seconds="$1"
  local url="http://localhost:${BACKEND_PORT}/"

  log "runner" "Waiting for backend readiness (up to ${timeout_seconds}s): ${url}"
  local start_ts
  start_ts="$(date +%s)"

  while true; do
    # If the process died, stop waiting and report clearly.
    if [[ -n "${BACKEND_PID}" ]] && ! kill -0 "${BACKEND_PID}" >/dev/null 2>&1; then
      log "runner" "ERROR: backend process exited before becoming ready."
      return 1
    fi

    if http_ready_check "${url}"; then
      log "runner" "Backend is responding."
      return 0
    fi

    local now_ts
    now_ts="$(date +%s)"
    if (( now_ts - start_ts >= timeout_seconds )); then
      log "runner" "ERROR: backend did not become ready within ${timeout_seconds}s."
      return 1
    fi

    sleep 0.5
  done
}

log "runner" "Launching backend..."
if ! start_backend; then
  log "runner" "Startup failed. See backend logs above."
  cleanup
  exit 3
fi

if ! wait_for_backend_ready "${STARTUP_TIMEOUT_SECONDS}"; then
  log "runner" "Startup failed (readiness check). Common causes:"
  log "runner" " - Port is in use (if another service bound between preflight and start)"
  log "runner" " - Missing environment variables / DB connection issues"
  log "runner" " - Application error during startup"
  log "runner" "Try: BACKEND_PORT=0 ./script.sh"
  cleanup
  exit 3
fi

log "runner" "Backend running:"
log "runner" " - Backend: http://localhost:${BACKEND_PORT} (docs: http://localhost:${BACKEND_PORT}/docs)"
log "runner" "Press Ctrl+C to stop."

# Wait until backend exits; if it exits unexpectedly, report and exit non-zero.
set +e
wait "${BACKEND_PID}"
backend_exit_code="$?"
set -e

if [[ "${backend_exit_code}" != "0" ]]; then
  log "runner" "Backend exited with code ${backend_exit_code}."
fi

cleanup
exit "${backend_exit_code}"
