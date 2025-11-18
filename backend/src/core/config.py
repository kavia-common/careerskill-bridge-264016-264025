from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.

    Note:
    - Do not hardcode secrets. Provide via environment variables or use defaults only for local dev.
    """

    APP_NAME: str = Field(default="SkillBridge LMS Backend", description="Application display name")
    VERSION: str = Field(default="0.1.0", description="Application version")
    DESCRIPTION: str = Field(
        default="Backend API for SkillBridge LMS - modular learning, mentorship, and job tools.",
        description="App description for OpenAPI docs",
    )

    # Security
    SECRET_KEY: str = Field(default="CHANGE_ME_DEV_ONLY", description="Secret key for JWT signing (dev default)")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["*"],  # Allow all in dev. Override in production.
        description="Allowed CORS origins",
    )

    # Database
    DATABASE_URL: AnyUrl | str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database URL. e.g., sqlite:///./app.db or postgres://...",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
