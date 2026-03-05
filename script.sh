#!/usr/bin/env bash
# SkillBridge backend runner (manual local run)
#
# Usage:
#   ./script.sh                # start backend on 0.0.0.0:3001
#   INSTALL_DEPS=1 ./script.sh # (optional) install python deps first
#
# Notes:
# - The backend reads configuration from a .env file located either at the repo root
#   or inside backend/ (Pydantic settings).
# - The preview system expects the backend on port 3001.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/backend"

if [[ ! -d "${BACKEND_DIR}" ]]; then
  echo "ERROR: backend directory not found at: ${BACKEND_DIR}" >&2
  exit 1
fi

cd "${BACKEND_DIR}"

if [[ "${INSTALL_DEPS:-0}" == "1" ]]; then
  if [[ ! -f "requirements.txt" ]]; then
    echo "ERROR: requirements.txt not found in $(pwd)" >&2
    exit 1
  fi

  # Assumes you already have python/pip available (ideally in a virtualenv).
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt
else
  # We assume dependencies are already installed (common in container/CI environments).
  # If you hit ImportError/ModuleNotFoundError, rerun with INSTALL_DEPS=1.
  :
fi

# Force the expected preview port unless the user explicitly overrides PORT in their environment.
export PORT="${PORT:-3001}"
export HOST="${HOST:-0.0.0.0}"

# Run the backend (this calls uvicorn internally with sane defaults).
exec python -m src.api.serve
