from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from src.db.base import Base


class User(Base):
    """User account representing a learner or mentor."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_mentor = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    attempts = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")
    progresses = relationship("Progress", back_populates="user", cascade="all, delete-orphan")
    mentor_profile = relationship("MentorProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    mentorship_requests = relationship(
        "MentorshipRequest", back_populates="user", cascade="all, delete-orphan", foreign_keys="MentorshipRequest.user_id"
    )
    mentorship_assignments = relationship(
        "MentorshipRequest",
        back_populates="mentor",
        cascade="all, delete-orphan",
        foreign_keys="MentorshipRequest.mentor_id",
    )
    portfolio_items = relationship("PortfolioItem", back_populates="user", cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    language_preferences = relationship("LanguagePreference", back_populates="user", cascade="all, delete-orphan")
