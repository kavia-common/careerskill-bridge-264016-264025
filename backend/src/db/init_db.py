from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.models.content import Lesson, Module, Question, Quiz
from src.models.user import User
from src.models.mentorship import MentorProfile
from src.models.extras import ResumeTemplate, InterviewQuestion


def _ensure_demo_learning_content(db: Session) -> None:
    """
    Ensure minimal module/lessons/quiz data and a demo learner exist.
    Idempotent: checks presence by natural keys/titles and returns if present.
    """
    # Ensure demo user
    demo_user = db.query(User).filter(User.email == "demo@example.com").first()
    if not demo_user:
        demo_user = User(
            email="demo@example.com",
            full_name="Demo User",
            hashed_password=hash_password("demo1234"),
            is_active=True,
        )
        db.add(demo_user)
        db.flush()

    # Ensure module
    module = db.query(Module).filter(Module.title == "Intro to SkillBridge").first()
    if not module:
        module = Module(title="Intro to SkillBridge", description="Get started with the SkillBridge LMS.")
        db.add(module)
        db.flush()

    # Ensure lessons
    lesson_specs = [
        ("Welcome", 1, "Welcome to SkillBridge!"),
        ("Navigation", 2, "How to navigate modules and lessons."),
    ]
    for title, order_idx, content in lesson_specs:
        exists = (
            db.query(Lesson)
            .filter(Lesson.module_id == module.id, Lesson.title == title, Lesson.order_index == order_idx)
            .first()
        )
        if not exists:
            db.add(Lesson(module_id=module.id, title=title, content=content, order_index=order_idx))
    db.flush()

    # Ensure quiz
    quiz = db.query(Quiz).filter(Quiz.module_id == module.id, Quiz.title == "Getting Started Quiz").first()
    if not quiz:
        quiz = Quiz(module_id=module.id, title="Getting Started Quiz")
        db.add(quiz)
        db.flush()

    # Ensure questions
    q_specs = [
        (
            "What does LMS stand for?",
            "Learning Management System",
            "Local Media Server",
            "Linear Model Strategy",
            "Least Mean Squares",
            "A",
        ),
        (
            "How many lessons were created in this module?",
            "1",
            "2",
            "3",
            "4",
            "B",
        ),
    ]
    for prompt, a, b, c, d, correct in q_specs:
        exists = db.query(Question).filter(Question.quiz_id == quiz.id, Question.prompt == prompt).first()
        if not exists:
            db.add(
                Question(
                    quiz_id=quiz.id,
                    prompt=prompt,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    option_d=d,
                    correct_option=correct,
                )
            )
    db.flush()


def _ensure_demo_mentors(db: Session) -> None:
    """
    Ensure demo mentors and corresponding MentorProfile entries exist.
    Idempotent by unique email and one-to-one profile.
    """
    mentors = [
        {
            "email": "mentor.alex@example.com",
            "full_name": "Alex Mentor",
            "expertise": "Data Analytics",
            "bio": "Data analyst with 8+ years in BI and visualization.",
        },
        {
            "email": "mentor.sofia@example.com",
            "full_name": "Sofia Guide",
            "expertise": "Digital Marketing",
            "bio": "Performance marketer focusing on paid search and SEO.",
        },
    ]
    for m in mentors:
        user = db.query(User).filter(User.email == m["email"]).first()
        if not user:
            user = User(
                email=m["email"],
                full_name=m["full_name"],
                hashed_password=hash_password("mentor1234"),
                is_active=True,
                is_mentor=True,
            )
            db.add(user)
            db.flush()
        else:
            # if existing user is not flagged as mentor, set it
            if not user.is_mentor:
                user.is_mentor = True

        # Ensure MentorProfile
        profile = db.query(MentorProfile).filter(MentorProfile.user_id == user.id).first()
        if not profile:
            db.add(MentorProfile(user_id=user.id, bio=m["bio"], expertise=m["expertise"]))
    db.flush()


def _ensure_interview_questions(db: Session) -> None:
    """
    Ensure a couple of interview questions exist for demo purposes.
    Idempotent by (category, question) tuple.
    """
    iq_specs = [
        ("general", "Tell me about yourself.", "Structure with present-past-future; keep it concise."),
        ("data_analytics", "How would you handle missing data?", "Discuss imputation, dropping, or model-based methods."),
    ]
    for category, question, hint in iq_specs:
        exists = (
            db.query(InterviewQuestion)
            .filter(InterviewQuestion.category == category, InterviewQuestion.question == question)
            .first()
        )
        if not exists:
            db.add(InterviewQuestion(category=category, question=question, answer_hint=hint))
    db.flush()


def _ensure_resume_template(db: Session) -> None:
    """
    Ensure a basic resume template entry exists.
    Idempotent by template_key uniqueness.
    """
    key = "basic-classic"
    exists = db.query(ResumeTemplate).filter(ResumeTemplate.template_key == key).first()
    if not exists:
        db.add(
            ResumeTemplate(
                name="Basic Classic",
                description="Clean one-page layout focusing on experience and skills.",
                template_key=key,
            )
        )
    db.flush()


def create_initial_data(db: Session) -> None:
    """
    Seed minimal demo data:
    - A demo user + learning content (module, lessons, quiz, questions)
    - Demo mentors with MentorProfile
    - A couple of InterviewQuestion entries
    - One ResumeTemplate
    Idempotent by checking existence before inserts; safe to run on every startup.
    """
    _ensure_demo_learning_content(db)
    _ensure_demo_mentors(db)
    _ensure_interview_questions(db)
    _ensure_resume_template(db)
