from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import logging

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import get_settings

logger = logging.getLogger(__name__)


def _ensure_passlib_bcrypt_compat() -> None:
    """
    Ensure passlib's bcrypt handler can read the bcrypt version.

    Contract:
    - Inputs: none
    - Outputs: none
    - Side effects: may set `bcrypt.__about__.__version__` dynamically if missing.
    - Errors: never raises; logs at debug on patch, warning on unexpected failure.

    Why:
    - passlib 1.7.4 expects `bcrypt.__about__.__version__`, but bcrypt 4.x removed it.
      This triggers noisy "(trapped) error reading bcrypt version" logs and can break
      hashing/verification in some environments.
    """
    try:
        import bcrypt  # type: ignore

        if not hasattr(bcrypt, "__about__"):
            bcrypt.__about__ = type("about", (), {"__version__": bcrypt.__version__})
            logger.debug("Applied bcrypt/passlib compatibility shim (added bcrypt.__about__.__version__).")
    except Exception:
        # Never block app startup due to best-effort compatibility patch.
        logger.warning("Failed to apply bcrypt/passlib compatibility shim.", exc_info=True)


_ensure_passlib_bcrypt_compat()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return pwd_context.hash(password)


# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# PUBLIC_INTERFACE
def create_access_token(subject: str | Any, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token for the given subject.

    Parameters:
    - subject: Identifier for the user (e.g., user ID or email)
    - expires_delta: Optional TTL for the token; default 60 minutes

    Returns:
    - Encoded JWT as string
    """
    settings = get_settings()
    to_encode = {"sub": str(subject), "iat": datetime.now(tz=timezone.utc)}
    expire = datetime.now(tz=timezone.utc) + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


# PUBLIC_INTERFACE
def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT token.

    Raises:
    - JWTError if token is invalid/expired.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError as exc:
        raise exc
