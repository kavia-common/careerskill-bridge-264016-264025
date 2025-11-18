from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db
from src.api.schemas import QuizOut, QuizQuestionOut, QuizResult, QuizSubmitRequest
from src.models.content import Question, Quiz
from src.models.tracking import Attempt
from src.models.user import User

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


# PUBLIC_INTERFACE
@router.post("/{module_id}/start", response_model=QuizOut, summary="Start quiz for module")
def start_quiz(module_id: int, _: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Start a quiz for a given module. Returns quiz with questions (without answers).
    """
    quiz = db.query(Quiz).filter(Quiz.module_id == module_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    questions = [
        QuizQuestionOut(
            id=q.id,
            prompt=q.prompt,
            option_a=q.option_a,
            option_b=q.option_b,
            option_c=q.option_c,
            option_d=q.option_d,
        )
        for q in quiz.questions
    ]
    return QuizOut(id=quiz.id, title=quiz.title, questions=questions)


# PUBLIC_INTERFACE
@router.post("/{quiz_id}/submit", response_model=QuizResult, summary="Submit quiz answers")
def submit_quiz(
    quiz_id: int,
    payload: QuizSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit answers and return a simple score in [0..100].
    """
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    q_by_id: dict[int, Question] = {q.id: q for q in quiz.questions}
    correct = 0
    for qid, ans in payload.answers.items():
        q = q_by_id.get(qid)
        if q and isinstance(ans, str) and ans.upper().strip() == q.correct_option.upper().strip():
            correct += 1
    total = max(1, len(q_by_id))
    score = (correct / total) * 100.0
    attempt = Attempt(user_id=user.id, quiz_id=quiz.id, score=score)
    db.add(attempt)
    return QuizResult(score=round(score, 2))
