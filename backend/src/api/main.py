from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.db.session import engine, db_session
from src.db.base import Base
from src.db.init_db import create_initial_data

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

# Prefer fine-grained CORS settings if provided, else fall back to simple defaults
allow_origins = settings.ALLOWED_ORIGINS or settings.CORS_ORIGINS
allow_methods = settings.ALLOWED_METHODS or ["*"]
allow_headers = settings.ALLOWED_HEADERS or ["*"]

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
    """
    # Create tables (for dev convenience; migrations are also provided)
    Base.metadata.create_all(bind=engine)

    # Seed minimal data
    with db_session() as db:
        create_initial_data(db)


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """
    Health check endpoint.

    Returns:
    - message: Healthy
    """
    return {"message": "Healthy"}
