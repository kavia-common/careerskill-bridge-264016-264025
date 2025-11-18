from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import MentorOut, MentorshipRequestIn, MentorshipRequestOut
from src.models.mentorship import MentorProfile, MentorshipRequest
from src.models.user import User

router = APIRouter(prefix="/mentorship", tags=["mentorship"])


# PUBLIC_INTERFACE
@router.get("/mentors", response_model=list[MentorOut], summary="List mentors")
def list_mentors(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return available mentors with minimal info.
    """
    profiles = db.query(MentorProfile).all()
    out: list[MentorOut] = []
    for p in profiles:
        out.append(
            MentorOut(
                id=p.user_id,
                full_name=p.user.full_name if p.user else None,
                expertise=p.expertise,
                bio=p.bio,
            )
        )
    return out


# PUBLIC_INTERFACE
@router.post("/requests", response_model=MentorshipRequestOut, summary="Create mentorship request")
def create_request(
    payload: MentorshipRequestIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a mentorship request to a mentor.
    """
    if user.id == payload.mentor_id:
        raise HTTPException(status_code=400, detail="Cannot request yourself")
    # ensure mentor exists and is mentor
    mentor = db.query(User).filter(User.id == payload.mentor_id, User.is_mentor.is_(True)).first()
    if not mentor:
        raise HTTPException(status_code=404, detail="Mentor not found")
    req = MentorshipRequest(user_id=user.id, mentor_id=payload.mentor_id, message=payload.message)
    db.add(req)
    db.flush()
    return MentorshipRequestOut(id=req.id, mentor_id=req.mentor_id, status=req.status)
