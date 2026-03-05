from typing import Optional
import logging

from fastapi import Depends, HTTPException, Header
from jose import JWTError
from sqlalchemy.orm import Session

from src.core.security import decode_token
from src.db.session import db_session
from src.models.user import User

logger = logging.getLogger(__name__)


def _extract_bearer_token(*candidates: Optional[str]) -> Optional[str]:
    """
    Extract a bearer token from a set of header candidates.

    Contract:
    - Inputs: one or more header values (strings) which may be None.
    - Output: token string if found, else None.
    - Parsing rules:
      - Accepts "Bearer <token>" (case-insensitive scheme).
      - Also accepts raw token value (no scheme) when provided via alternative headers.
    """
    for value in candidates:
        if not value:
            continue
        v = value.strip()
        if not v:
            continue
        if v.lower().startswith("bearer "):
            token = v.split(" ", 1)[1].strip()
            return token or None
        # Allow raw token (useful for X-Access-Token style headers)
        return v
    return None


# PUBLIC_INTERFACE
def get_db():
    """Yield a SQLAlchemy Session from the pooled session maker."""
    with db_session() as db:
        yield db


# PUBLIC_INTERFACE
def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_authorization: Optional[str] = Header(default=None, alias="X-Authorization"),
    x_access_token: Optional[str] = Header(default=None, alias="X-Access-Token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve and return the authenticated user from a JWT token passed via headers.

    Contract:
    - Inputs (headers):
      - Authorization: "Bearer <token>" (preferred)
      - X-Authorization: "Bearer <token>" (proxy fallback)
      - X-Access-Token: "<token>" (proxy fallback)
    - Output:
      - User ORM instance for authenticated user.
    - Errors:
      - 401 Not authenticated: missing token
      - 401 Invalid token: token decode/validation fails
      - 401 Invalid token payload: missing required `sub`
      - 401 User not found or inactive: no matching active user
    """
    token = _extract_bearer_token(authorization, x_authorization, x_access_token)
    if not token:
        # Keep same outward behavior, but log enough for future debugging.
        logger.info(
            "Auth failed: missing bearer token (Authorization/X-Authorization/X-Access-Token all empty or invalid)."
        )
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # sub is user id or email; try id int first then email
    user: Optional[User] = None
    if str(sub).isdigit():
        user = db.query(User).filter(User.id == int(sub)).first()
    if not user:
        user = db.query(User).filter(User.email == str(sub)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user
