from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import (
    InterviewSimulateIn,
    InterviewSimulateOut,
    ResumePreviewIn,
    ResumePreviewOut,
)
from src.models.user import User

router = APIRouter(prefix="/jobtools", tags=["jobtools"])


# PUBLIC_INTERFACE
@router.post("/resume/preview", response_model=ResumePreviewOut, summary="Resume preview")
def resume_preview(payload: ResumePreviewIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return a minimal preview summary and basic tips. No external services used.
    """
    text = (payload.content or "").strip()
    summary = text[:140] + ("..." if len(text) > 140 else "")
    tips = [
        "Use active verbs.",
        "Quantify achievements.",
        "Keep it concise (1-2 pages).",
    ]
    return ResumePreviewOut(summary=summary, tips=tips)


# PUBLIC_INTERFACE
@router.post("/interview/simulate", response_model=InterviewSimulateOut, summary="Interview simulate")
def interview_simulate(payload: InterviewSimulateIn, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return a small set of role-based mock interview questions (static demo).
    """
    role = (payload.role or "general").lower()
    base = [
        "Tell me about yourself.",
        "Describe a challenging problem you solved.",
    ]
    if "data" in role:
        base += ["How would you handle missing data?", "Explain the difference between mean and median."]
    elif "marketing" in role:
        base += ["How do you evaluate campaign ROI?", "What KPIs would you track for a brand launch?"]
    elif "engineer" in role or "developer" in role:
        base += ["What is the time complexity of binary search?", "Explain REST vs. WebSocket."]
    return InterviewSimulateOut(questions=base[:5])
