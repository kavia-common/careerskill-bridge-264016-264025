from typing import List, Optional
from pydantic import BaseModel, Field


# Auth
class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


# User
class UserMe(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    is_mentor: bool


# Content
class ModuleOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None


class LessonOut(BaseModel):
    id: int
    module_id: int
    title: str
    content: Optional[str] = None
    order_index: int


class QuizQuestionOut(BaseModel):
    id: int
    prompt: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class QuizOut(BaseModel):
    id: int
    title: str
    questions: List[QuizQuestionOut]


class QuizSubmitRequest(BaseModel):
    answers: dict[int, str] = Field(..., description="Map question_id -> selected option A-D")


class QuizResult(BaseModel):
    score: float


# Progress
class ProgressOut(BaseModel):
    module_id: int
    status: str
    progress_percent: float
    current_lesson_id: Optional[int] = None


# Mentorship
class MentorOut(BaseModel):
    id: int
    full_name: Optional[str] = None
    expertise: Optional[str] = None
    bio: Optional[str] = None


class MentorshipRequestIn(BaseModel):
    mentor_id: int
    message: Optional[str] = None


class MentorshipRequestOut(BaseModel):
    id: int
    mentor_id: int
    status: str


# Portfolio
class PortfolioItemIn(BaseModel):
    title: str
    description: Optional[str] = None
    url: Optional[str] = None


class PortfolioItemOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    url: Optional[str] = None


# Notifications
class NotificationOut(BaseModel):
    id: int
    message: str
    is_read: bool


# Job tools
class ResumePreviewIn(BaseModel):
    content: str = Field(..., description="Raw resume text/markdown")


class ResumePreviewOut(BaseModel):
    summary: str
    tips: List[str]


class InterviewSimulateIn(BaseModel):
    role: str
    level: Optional[str] = "junior"


class InterviewSimulateOut(BaseModel):
    questions: List[str]
