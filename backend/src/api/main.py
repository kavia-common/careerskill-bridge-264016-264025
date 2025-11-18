from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.db.session import engine, db_session
from src.db.base import Base
from src.db.init_db import create_initial_data

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    openapi_tags=[
        {"name": "health", "description": "Service health and info"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """
    Health check endpoint.

    Returns:
    - message: Healthy
    """
    return {"message": "Healthy"}
