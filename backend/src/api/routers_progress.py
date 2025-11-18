from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import ProgressOut
from src.models.tracking import Progress
from src.models.user import User

router = APIRouter(prefix="/progress", tags=["progress"])


# PUBLIC_INTERFACE
@router.get("", response_model=list[ProgressOut], summary="My progress")
def my_progress(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return per-module progress for current user.
    """
    rows = db.query(Progress).filter(Progress.user_id == user.id).all()
    return [
        ProgressOut(
            module_id=p.module_id,
            status=p.status,
            progress_percent=p.progress_percent,
            current_lesson_id=p.current_lesson_id,
        )
        for p in rows
    ]
