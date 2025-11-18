from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import UserMe
from src.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


# PUBLIC_INTERFACE
@router.get("/me", response_model=UserMe, summary="Current user profile")
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return minimal information for the currently authenticated user.
    """
    return UserMe(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_mentor=current_user.is_mentor,
    )
