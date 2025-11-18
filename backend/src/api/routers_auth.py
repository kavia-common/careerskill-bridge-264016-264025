from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from src.core.security import create_access_token, verify_password, hash_password
from src.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


# PUBLIC_INTERFACE
@router.post("/register", response_model=TokenResponse, summary="Register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new user and return an access token.

    Body:
    - email
    - password
    - full_name (optional)
    """
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        is_active=True,
    )
    db.add(user)
    db.flush()
    token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=8))
    return TokenResponse(access_token=token, token_type="bearer")


# PUBLIC_INTERFACE
@router.post("/login", response_model=TokenResponse, summary="Login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return an access token.

    Body:
    - email
    - password
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(subject=str(user.id), expires_delta=timedelta(hours=8))
    return TokenResponse(access_token=token, token_type="bearer")
