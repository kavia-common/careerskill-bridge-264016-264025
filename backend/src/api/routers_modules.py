from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import LessonOut, ModuleOut
from src.models.content import Lesson, Module
from src.models.user import User

router = APIRouter(prefix="/modules", tags=["modules"])


# PUBLIC_INTERFACE
@router.get("", response_model=list[ModuleOut], summary="List modules")
def list_modules(_: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return a minimal list of learning modules.
    """
    modules = db.query(Module).all()
    return [ModuleOut(id=m.id, title=m.title, description=m.description) for m in modules]


# PUBLIC_INTERFACE
@router.get("/{module_id}", response_model=ModuleOut, summary="Module detail")
def module_detail(module_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return a single module by id.
    """
    m = db.query(Module).filter(Module.id == module_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Module not found")
    return ModuleOut(id=m.id, title=m.title, description=m.description)


router_lessons = APIRouter(prefix="/lessons", tags=["lessons"])


# PUBLIC_INTERFACE
@router_lessons.get("/{lesson_id}", response_model=LessonOut, summary="Get lesson")
def get_lesson(lesson_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Return a lesson content by id.
    """
    l = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonOut(
        id=l.id,
        module_id=l.module_id,
        title=l.title,
        content=l.content,
        order_index=l.order_index,
    )


# PUBLIC_INTERFACE
@router_lessons.post("/{lesson_id}/complete", summary="Complete lesson")
def complete_lesson(lesson_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Mark a lesson as completed and update simple progress percent within its module.
    """
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # Update naive progress: percent based on number of lessons completed, tracked via current_lesson_id bump.
    from sqlalchemy import func
    from src.models.tracking import Progress  # local import to avoid cycles

    total = db.query(func.count(Lesson.id)).filter(Lesson.module_id == lesson.module_id).scalar() or 1
    prog = (
        db.query(Progress)
        .filter(Progress.user_id == user.id, Progress.module_id == lesson.module_id)
        .first()
    )
    if not prog:
        prog = Progress(user_id=user.id, module_id=lesson.module_id, current_lesson_id=lesson.id, progress_percent=0.0)
        db.add(prog)
        db.flush()
    prog.current_lesson_id = lesson.id
    # naive increment: set progress to min(100, current index / total * 100)
    idx = lesson.order_index if lesson.order_index else 1
    percent = max(0.0, min(100.0, (idx / float(total)) * 100.0))
    prog.progress_percent = percent
    if percent >= 100.0:
        prog.status = "completed"
    return {"status": "ok", "progress_percent": round(prog.progress_percent, 2)}
