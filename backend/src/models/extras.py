from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.db.base import Base


class PortfolioItem(Base):
    """A portfolio item created by a user to showcase skills."""
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="portfolio_items")


class Certificate(Base):
    """A certificate awarded to a user."""
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(Integer, ForeignKey("modules.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    issued_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="certificates")


class Notification(Base):
    """Notification sent to a user (e.g., lesson reminder)."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class ResumeTemplate(Base):
    """Resume template metadata."""
    __tablename__ = "resume_templates"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_key = Column(String(255), unique=True, nullable=False)


class InterviewQuestion(Base):
    """Interview question bank item."""
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True)
    category = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    answer_hint = Column(Text, nullable=True)


class LanguagePreference(Base):
    """Language preference per user."""
    __tablename__ = "language_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    language_code = Column(String(10), nullable=False, default="en")

    user = relationship("User", back_populates="language_preferences")
