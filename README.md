# careerskill-bridge-264016-264025

This repository contains the **SkillBridge backend** (FastAPI). The **React frontend** lives in a sibling workspace folder:
`../careerskill-bridge-264016-264026/frontend_web_app`.

## All-in-one (manual) run script

A root-level `script.sh` is provided to install dependencies (idempotently) and run **both** backend + frontend together.

1) Ensure the script is executable:

```bash
chmod +x ./script.sh
```

2) Run everything:

```bash
./script.sh
```

Defaults:
- Frontend: http://localhost:3000
- Backend: http://localhost:3001 (docs: http://localhost:3001/docs)

Optional flags/env vars:
- `INSTALL_DEPS=0 ./script.sh` to skip installs
- `FORCE_INSTALL=1 ./script.sh` to force re-install (npm + pip)
- `FRONTEND_PORT=3000 BACKEND_PORT=3001 ./script.sh` to override ports (must be different)

> Note: This script is for **manual development runs** and does not modify or interfere with the PreviewManager port/command configuration.

## Frontend integration quickstart

- Copy `../careerskill-bridge-264016-264026/frontend_web_app/.env.example` to `.env` (in the same frontend folder) and adjust:
  - `REACT_APP_API_BASE` to the backend base URL (local dev: `http://localhost:3001`)
  - `REACT_APP_WS_URL` to `ws://localhost:3001/ws/notifications`

Backend CORS automatically includes configured origins plus the actual frontend URL and localhost:3000 for dev.

## Backend env sample

- See `backend/.env.example` for minimal variables (`PORT`, `FRONTEND_URL`, `BACKEND_URL`, `WS_URL`, `CORS_ORIGINS`, `SECRET_KEY`).
- Place the `.env` file either at repo root or in `backend/`; `pydantic-settings` will read `.env`.

## OpenAPI

- The backend publishes OpenAPI at `/openapi.json` and docs at `/docs`.
- To re-generate the repo copy of the spec: `python -m src.api.generate_openapi` (writes `backend/interfaces/openapi.json`).
