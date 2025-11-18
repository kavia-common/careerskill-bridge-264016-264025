# SkillBridge Backend: Quick Integration Setup

This guide ensures the backend is reachable from the React frontend and documents essential envs and smoke tests.

1) Environment variables (.env at repo root or backend/)
- PORT=3001                # Backend service port (default 3001)
- FRONTEND_URL=<https://your-frontend-host:3000>  # Used to augment CORS
- BACKEND_URL=<https://your-backend-host:3001>
- WS_URL=<wss://your-backend-host:3001/ws/notifications>
- CORS_ORIGINS=<csv list>  # Optional; backend also auto-adds FRONTEND_URL and localhost:3000
- SECRET_KEY=<change-me>   # For JWT signing (dev default exists but change for non-dev)

2) CORS behavior
- The backend uses ALLOWED_ORIGINS/CORS_ORIGINS and automatically augments with:
  - FRONTEND_URL or REACT_APP_FRONTEND_URL (if present)
  - http(s)://localhost:3000
This ensures the active frontend origin is included for dev and integration.

3) Port binding
- The server binds to HOST=0.0.0.0 and PORT from env (default 3001).
- Invalid/missing PORT falls back to 3001.

4) Frontend envs (React)
- REACT_APP_API_BASE = https://<backend-host>:3001
- REACT_APP_WS_URL = wss://<backend-host>:3001/ws/notifications
Notes:
- Ensure your build system injects these at compile-time (Create React App or Vite style).
- For local dev, set REACT_APP_API_BASE to http://localhost:3001 and REACT_APP_WS_URL to ws://localhost:3001/ws/notifications.

5) OpenAPI spec
- Live docs: GET /docs
- JSON spec: GET /openapi.json
- Regenerate repo copy: `python -m src.api.generate_openapi` (writes backend/interfaces/openapi.json)

6) E2E smoke path (Authorization: Bearer <token>)
1) POST /auth/register -> token
2) GET /modules
3) GET /lessons/{id} -> POST /lessons/{id}/complete
4) POST /quizzes/{moduleId}/start -> POST /quizzes/{quizId}/submit
5) GET /progress
6) GET /mentorship/mentors -> POST /mentorship/requests
7) GET /portfolio -> POST /portfolio -> PUT/DELETE /portfolio/{itemId}
8) GET /notifications
9) WebSocket: connect to /ws/notifications?token=<JWT>, send "ping" -> expect "pong"

7) Troubleshooting
- 401: Verify Authorization header "Bearer <token>".
- CORS blocked: Confirm FRONTEND_URL matches the origin and/or set a specific CORS_ORIGINS list.
- WS connect fails: Ensure REACT_APP_WS_URL points to /ws/notifications and token is present in the query string.
