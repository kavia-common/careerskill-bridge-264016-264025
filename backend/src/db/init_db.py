from sqlalchemy.orm import Session

from src.core.security import hash_password
from src.models.content import Lesson, Module, Question, Quiz
from src.models.user import User


def create_initial_data(db: Session) -> None:
    """
    Seed minimal demo data:
    - A demo user
    - One Module with 2 lessons and a quiz with 2 questions
    """
    # Check existing module
    existing_module = db.query(Module).filter(Module.title == "Intro to SkillBridge").first()
    if existing_module:
        return

    # Demo user
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

    module = Module(title="Intro to SkillBridge", description="Get started with the SkillBridge LMS.")
    db.add(module)
    db.flush()

    lesson1 = Lesson(module_id=module.id, title="Welcome", content="Welcome to SkillBridge!", order_index=1)
    lesson2 = Lesson(module_id=module.id, title="Navigation", content="How to navigate modules and lessons.", order_index=2)
    db.add_all([lesson1, lesson2])
    db.flush()

    quiz = Quiz(module_id=module.id, title="Getting Started Quiz")
    db.add(quiz)
    db.flush()

    q1 = Question(
        quiz_id=quiz.id,
        prompt="What does LMS stand for?",
        option_a="Learning Management System",
        option_b="Local Media Server",
        option_c="Linear Model Strategy",
        option_d="Least Mean Squares",
        correct_option="A",
    )
    q2 = Question(
        quiz_id=quiz.id,
        prompt="How many lessons were created in this module?",
        option_a="1",
        option_b="2",
        option_c="3",
        option_d="4",
        correct_option="B",
    )
    db.add_all([q1, q2])
    db.flush()
