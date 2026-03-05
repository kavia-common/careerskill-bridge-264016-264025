# careerskill-bridge-264016-264025

This repository contains the **SkillBridge backend** (FastAPI). The **React frontend** lives in a sibling workspace folder:
`../careerskill-bridge-264016-264026/frontend_web_app`.

## Backend-only run script

A root-level `script.sh` is provided to install backend dependencies (idempotently) and run **ONLY** the backend.

1) Ensure the script is executable:

```bash
chmod +x ./script.sh
```

2) Run the backend:

```bash
./script.sh
```

Defaults:
- Backend: http://localhost:3001 (docs: http://localhost:3001/docs)

Optional flags/env vars:
- `INSTALL_DEPS=0 ./script.sh` to skip pip installs
- `FORCE_INSTALL=1 ./script.sh` to force re-install (pip)
- `BACKEND_PORT=3001 BACKEND_HOST=0.0.0.0 ./script.sh` to override bind address/port

> Note: This script is for **manual development runs** and does not modify or interfere with the PreviewManager port/command configuration.

## Frontend integration quickstart

- Run the frontend separately from the sibling workspace folder:
  - `../careerskill-bridge-264016-264026/frontend_web_app`
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
