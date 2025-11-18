from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from src.core.config import get_settings
from src.db.session import engine, db_session
from src.db.base import Base
from src.db.init_db import create_initial_data

logger = logging.getLogger(__name__)

# Load validated settings; Settings now ignores unknown env vars per model_config.extra='ignore'
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_tags=[
        {"name": "health", "description": "Service health and info"},
    ],
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
