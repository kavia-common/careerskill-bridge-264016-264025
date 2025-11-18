# careerskill-bridge-264016-264025

Frontend integration quickstart:
- Copy careerskill-bridge-264016-264026/frontend_web_app/.env.example to .env and adjust:
  - REACT_APP_API_BASE to the backend base URL (default https://<host>:3001)
  - REACT_APP_WS_URL to wss(s)://<host>:3001/ws/notifications
- Backend CORS automatically includes configured origins plus the actual frontend URL and localhost:3000 for dev.

Backend env sample:
- See backend/.env.example for minimal variables (PORT, FRONTEND_URL, BACKEND_URL, WS_URL, CORS_ORIGINS, SECRET_KEY).
- Place the .env file either at repo root or in backend/; pydantic-settings will read .env.

OpenAPI:
- The backend publishes OpenAPI at /openapi.json and docs at /docs.
- To re-generate the repo copy of the spec: `python -m src.api.generate_openapi` (writes backend/interfaces/openapi.json).