import os

import uvicorn

from src.api.main import app
from src.core.config import get_settings

# PUBLIC_INTERFACE
def run() -> None:
    """Entrypoint to serve the FastAPI app with sane defaults.

    - Host: 0.0.0.0
    - Port: environment variable PORT (if set) else Settings.PORT else 3001
    - Workers: single process by default (safe in dev/CI)
    """
    settings = get_settings()
    host = os.environ.get("HOST") or settings.UVICORN_HOST or "0.0.0.0"
    # Environment PORT should take precedence in many platforms
    port_str = os.environ.get("PORT")
    try:
        port = int(port_str) if port_str else int(settings.PORT) if settings.PORT else 3001
    except Exception:
        port = 3001

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run()
