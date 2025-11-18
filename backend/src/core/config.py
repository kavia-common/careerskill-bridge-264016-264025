from functools import lru_cache
from typing import List

from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.

    Note:
    - Do not hardcode secrets. Provide via environment variables or use defaults only for local dev.
    """

    # Basic app info
    APP_NAME: str = Field(default="SkillBridge LMS Backend", description="Application display name")
    VERSION: str = Field(default="0.1.0", description="Application version")
    DESCRIPTION: str = Field(
        default="Backend API for SkillBridge LMS - modular learning, mentorship, and job tools.",
        description="App description for OpenAPI docs",
    )

    # Security
    SECRET_KEY: str = Field(default="CHANGE_ME_DEV_ONLY", description="Secret key for JWT signing (dev default)")

    # CORS - allow list, will also accept comma-separated string via env
    CORS_ORIGINS: List[str] = Field(
        default=["*"],  # Allow all in dev. Override in production.
        description="Allowed CORS origins",
    )

    # Database
    DATABASE_URL: AnyUrl | str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database URL. e.g., sqlite:///./app.db or postgres://...",
    )

    # Common frontend-provided / deployment envs (ignored if unused elsewhere but defined to prevent 'extra' errors)
    BACKEND_URL: str | None = Field(default=None, description="Public backend URL base", alias="backend_url")
    FRONTEND_URL: str | None = Field(default=None, description="Public frontend URL base", alias="frontend_url")
    WS_URL: str | None = Field(default=None, description="Public websocket URL base", alias="ws_url")
    SITE_URL: str | None = Field(default=None, description="Site base URL for redirects", alias="site_url")

    # CORS fine-grained options, parsed from comma-separated strings if provided
    ALLOWED_ORIGINS: List[str] | None = Field(default=None, description="CORS allowed origins", alias="allowed_origins")
    ALLOWED_HEADERS: List[str] | None = Field(default=None, description="CORS allowed headers", alias="allowed_headers")
    ALLOWED_METHODS: List[str] | None = Field(default=None, description="CORS allowed methods", alias="allowed_methods")
    CORS_MAX_AGE: int | None = Field(default=None, description="CORS max age seconds", alias="cors_max_age")

    COOKIE_DOMAIN: str | None = Field(default=None, description="Cookie domain", alias="cookie_domain")
    TRUST_PROXY: bool | None = Field(default=None, description="Trust proxy headers (X-Forwarded-*)", alias="trust_proxy")
    HOST: str | None = Field(default=None, description="Host for app", alias="host")
    UVICORN_HOST: str | None = Field(default=None, description="Uvicorn host", alias="uvicorn_host")
    UVICORN_WORKERS: int | None = Field(default=None, description="Uvicorn workers", alias="uvicorn_workers")
    NODE_ENV: str | None = Field(default=None, description="Node-like environment label", alias="node_env")
    REQUEST_TIMEOUT_MS: int | None = Field(default=None, description="Request timeout ms", alias="request_timeout_ms")
    RATE_LIMIT_WINDOW_S: int | None = Field(default=None, description="Rate limit window seconds", alias="rate_limit_window_s")
    RATE_LIMIT_MAX: int | None = Field(default=None, description="Rate limit max requests per window", alias="rate_limit_max")
    PORT: int | None = Field(default=None, description="Service port", alias="port")

    # React-style variables (present in env but backend doesn't use them)
    REACT_APP_API_BASE: str | None = Field(default=None, description="React app API base")
    REACT_APP_BACKEND_URL: str | None = Field(default=None, description="React app backend URL")
    REACT_APP_FRONTEND_URL: str | None = Field(default=None, description="React app frontend URL")
    REACT_APP_WS_URL: str | None = Field(default=None, description="React app websocket URL")
    REACT_APP_NODE_ENV: str | None = Field(default=None, description="React app env")
    REACT_APP_NEXT_TELEMETRY_DISABLED: str | None = Field(default=None, description="Disable next telemetry")
    REACT_APP_ENABLE_SOURCE_MAPS: str | None = Field(default=None, description="Enable source maps")
    REACT_APP_PORT: str | None = Field(default=None, description="Frontend port")
    REACT_APP_TRUST_PROXY: str | None = Field(default=None, description="Trust proxy")
    REACT_APP_LOG_LEVEL: str | None = Field(default=None, description="Log level")
    REACT_APP_HEALTHCHECK_PATH: str | None = Field(default=None, description="Health path")
    REACT_APP_FEATURE_FLAGS: str | None = Field(default=None, description="Feature flags")
    REACT_APP_EXPERIMENTS_ENABLED: str | None = Field(default=None, description="Experiments toggle")

    # Pydantic v2 settings: ignore extra vars, case-insensitive, and read .env
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):  # noqa: D401
        """Allow CORS_ORIGINS to be provided as a comma-separated string or JSON-like list."""
        if v is None:
            return ["*"]
        if isinstance(v, str):
            # Split on comma and strip, ignore empty
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts or ["*"]
        return v

    @field_validator("ALLOWED_ORIGINS", "ALLOWED_HEADERS", "ALLOWED_METHODS", mode="before")
    @classmethod
    def parse_csv_lists(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(",") if p.strip()]
            return parts
        return v


# PUBLIC_INTERFACE
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
