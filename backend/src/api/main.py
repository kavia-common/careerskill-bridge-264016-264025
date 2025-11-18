from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.core.config import get_settings
from src.db.session import engine, db_session
from src.db.base import Base
from src.db.init_db import create_initial_data

# Routers
from src.api.routers_auth import router as auth_router
from src.api.routers_users import router as users_router
from src.api.routers_modules import router as modules_router, router_lessons as lessons_router
from src.api.routers_quizzes import router as quizzes_router
from src.api.routers_progress import router as progress_router
from src.api.routers_mentorship import router as mentorship_router
from src.api.routers_portfolio import router as portfolio_router
from src.api.routers_notifications import router as notifications_router
from src.api.routers_jobtools import router as jobtools_router
from src.api.routers_ws import router as ws_router

logger = logging.getLogger(__name__)

# Load validated settings
settings = get_settings()

openapi_tags = [
    {"name": "health", "description": "Service health and info"},
    {"name": "auth", "description": "Authentication (register/login)"},
    {"name": "users", "description": "User profile endpoints"},
    {"name": "modules", "description": "Learning modules"},
    {"name": "lessons", "description": "Lessons within modules"},
    {"name": "quizzes", "description": "Quizzes and results"},
    {"name": "progress", "description": "Learning progress"},
    {"name": "mentorship", "description": "Mentors and requests"},
    {"name": "portfolio", "description": "Portfolio items"},
    {"name": "notifications", "description": "Notifications list"},
    {"name": "jobtools", "description": "Resume and interview tools"},
    {"name": "websocket", "description": "Real-time notifications WebSocket"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_tags=openapi_tags,
)

def _ensure_list_str(value, default=None):
    """
    Normalize a value into a list[str].
    """
    if default is None:
        default = []
    if value is None:
        return list(default)
    if isinstance(value, (list, tuple)):
        return [str(v) for v in value]
    # single string => wrap
    return [str(value)]

# Prefer fine-grained CORS settings if provided, else fall back to simple defaults
allow_origins = _ensure_list_str(settings.ALLOWED_ORIGINS or settings.CORS_ORIGINS or ["*"], default=["*"])
allow_methods = _ensure_list_str(settings.ALLOWED_METHODS or ["*"], default=["*"])
allow_headers = _ensure_list_str(settings.ALLOWED_HEADERS or ["*"], default=["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=allow_methods,
    allow_headers=allow_headers,
)


@app.on_event("startup")
def on_startup() -> None:
    """
    Initialize database and run seed data on application startup.

    This will:
    - Create all tables if they do not exist (for dev)
    - Insert minimal demo data for UI integration

    Startup is hardened so DB issues do not prevent the app from binding to the port.
    """
    try:
        # Create tables (for dev convenience; migrations are also provided)
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB table creation failed on startup: %s", exc)

    # Seed minimal data (best-effort)
    try:
        with db_session() as db:
            create_initial_data(db)
    except Exception as exc:  # noqa: BLE001
        logger.warning("DB seed failed on startup (continuing service): %s", exc)


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """
    Health check endpoint.

    Returns:
    - message: Healthy
    """
    return {"message": "Healthy"}


# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(modules_router)
app.include_router(lessons_router)
app.include_router(quizzes_router)
app.include_router(progress_router)
app.include_router(mentorship_router)
app.include_router(portfolio_router)
app.include_router(notifications_router)
app.include_router(jobtools_router)
app.include_router(ws_router)
