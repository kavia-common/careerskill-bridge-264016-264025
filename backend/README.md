# SkillBridge LMS Backend (FastAPI)

- Service default port: 3001 (override with PORT env). If PORT is unset or invalid, the server binds to 3001.
- CORS: Uses ALLOWED_ORIGINS/CORS_ORIGINS and automatically augments with FRONTEND_URL/REACT_APP_FRONTEND_URL and http(s)://localhost:3000 for dev to ensure the actual frontend origin is included.
- WebSocket: /ws/notifications (see GET /ws/usage)

Environment variables (examples):
- PORT=3001
- FRONTEND_URL=https://vscode-internal-34534-beta.beta01.cloud.kavia.ai:3000
- BACKEND_URL=https://vscode-internal-34534-beta.beta01.cloud.kavia.ai:3001
- WS_URL=wss://vscode-internal-34534-beta.beta01.cloud.kavia.ai:3001/ws/notifications
- CORS_ORIGINS=https://vscode-internal-34534-beta.beta01.cloud.kavia.ai:3000

Frontend (React) expected envs:
- REACT_APP_API_BASE=https://vscode-internal-34534-beta.beta01.cloud.kavia.ai:3001
- REACT_APP_WS_URL=wss://vscode-internal-34534-beta.beta01.cloud.kavia.ai:3001/ws/notifications

OpenAPI:
- Live: GET /openapi.json, docs at /docs
- Regenerate repo copy: `python -m src.api.generate_openapi` (writes backend/interfaces/openapi.json)

Quick E2E smoke path (with Authorization: Bearer <token>):
1) POST /auth/register -> token
2) GET /modules
3) GET /lessons/{id} -> POST /lessons/{id}/complete
4) POST /quizzes/{moduleId}/start -> POST /quizzes/{quizId}/submit
5) GET /progress
6) GET /mentorship/mentors -> POST /mentorship/requests
7) GET /portfolio -> POST /portfolio -> PUT/DELETE /portfolio/{itemId}
8) GET /notifications
9) WebSocket: connect to /ws/notifications?token=<JWT>, send "ping" -> expect "pong"
