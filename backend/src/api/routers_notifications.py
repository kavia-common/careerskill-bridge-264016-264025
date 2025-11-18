from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import NotificationOut
from src.models.extras import Notification
from src.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


# PUBLIC_INTERFACE
@router.get("", response_model=list[NotificationOut], summary="List my notifications")
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Notification).filter(Notification.user_id == user.id).order_by(Notification.id.desc()).all()
    return [NotificationOut(id=n.id, message=n.message, is_read=n.is_read) for n in rows]
