# SkillBridge LMS Backend (FastAPI)

## Overview
This FastAPI service provides authentication, modular learning (modules, lessons, quizzes), progress tracking, mentorship, portfolio, notifications, and job tools. It exposes a REST API and a WebSocket for real-time notifications.

## Setup and Run
1. Create and activate a Python environment (3.11+ recommended), then install dependencies:
   - pip install -r requirements.txt
2. Create a .env file at the repo root or in backend/ with minimally the variables below.
3. Start the API:
   - python -m src.api.serve
   - This runs uvicorn with host 0.0.0.0 and port determined as described below.

You can also run via uvicorn explicitly if desired:
- uvicorn src.api.main:app --host 0.0.0.0 --port 3001

## Environment Variables
The configuration is defined in src/core/config.py (Pydantic Settings). Use these key variables:

- PORT: Service port (default 3001). If unset or invalid, the server binds to 3001.
- SECRET_KEY: Secret for JWT signing (use a strong, non-default value in production).
- DATABASE_URL: SQLAlchemy URL (default sqlite:///./app.db, supports postgres etc.).
- CORS_ORIGINS or ALLOWED_ORIGINS: Comma-separated list of allowed origins for CORS.
- FRONTEND_URL: Public frontend base URL (helps with CORS).
- BACKEND_URL: Public backend base URL.
- WS_URL: Public WebSocket base URL for notifications.

Optional helpers:
- HOST, UVICORN_HOST: Host binding overrides (default 0.0.0.0).
- REACT_APP_* variables may be present in env; they are ignored by the backend, but tolerated by settings.

CORS behavior: You can provide CORS_ORIGINS as a comma-separated list; ALLOWED_ORIGINS is also supported. Include your frontend origin(s) (e.g., http://localhost:3000) for local development.

## How Port and Host Are Determined
- src/api/serve.py uses environment PORT if set; otherwise Settings.PORT; if not valid, falls back to 3001.
- Host defaults to 0.0.0.0 (overridable via HOST or UVICORN_HOST).

## WebSocket
- Path: /ws/notifications
- Usage helper: GET /ws/usage
- Connect with query param token=<JWT>, for example: wss://<host>:3001/ws/notifications?token=<JWT>

## API Overview (selected endpoints)
- Health: GET /
- Auth: POST /auth/register, POST /auth/login
- Users: GET /users/me
- Modules: GET /modules, GET /modules/{module_id}
- Lessons: GET /lessons/{lesson_id}, POST /lessons/{lesson_id}/complete
- Quizzes: POST /quizzes/{module_id}/start, POST /quizzes/{quiz_id}/submit
- Progress: GET /progress
- Mentorship: GET /mentorship/mentors, POST /mentorship/requests
- Portfolio: GET /portfolio, POST /portfolio, PUT /portfolio/{item_id}, DELETE /portfolio/{item_id}
- Notifications: GET /notifications
- WebSocket help: GET /ws/usage

## OpenAPI
- Live spec: GET /openapi.json; interactive docs at /docs
- Regenerate repo copy: python -m src.api.generate_openapi (writes interfaces/openapi.json)

## E2E Smoke Checklist (API)
Use Authorization: Bearer <token> after registration/login.
1. POST /auth/register -> receive access_token
2. GET /modules
3. GET /lessons/{id} -> POST /lessons/{id}/complete
4. POST /quizzes/{module_id}/start -> POST /quizzes/{quiz_id}/submit
5. GET /progress
6. GET /mentorship/mentors -> POST /mentorship/requests
7. GET /portfolio -> POST /portfolio -> PUT/DELETE /portfolio/{item_id}
8. GET /notifications
9. WebSocket: connect to /ws/notifications?token=<JWT>; send "ping" and verify "pong"/welcome message
