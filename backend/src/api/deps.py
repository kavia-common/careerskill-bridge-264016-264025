from typing import Optional

from fastapi import Depends, HTTPException, Header
from jose import JWTError
from sqlalchemy.orm import Session

from src.core.security import decode_token
from src.db.session import db_session
from src.models.user import User


# PUBLIC_INTERFACE
def get_db():
    """Yield a SQLAlchemy Session from the pooled session maker."""
    with db_session() as db:
        yield db


# PUBLIC_INTERFACE
def get_current_user(
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> User:
    """
    Resolve and return the authenticated user from a Bearer JWT in the Authorization header.

    Parameters:
    - Authorization: "Bearer <token>"

    Returns:
    - User ORM instance

    Raises:
    - 401 if header/token invalid or user not found.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
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
