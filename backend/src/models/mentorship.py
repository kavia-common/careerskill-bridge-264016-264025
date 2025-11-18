from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.db.base import Base


class MentorProfile(Base):
    """Additional information for mentors."""
    __tablename__ = "mentor_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    bio = Column(Text, nullable=True)
    expertise = Column(String(255), nullable=True)

    user = relationship("User", back_populates="mentor_profile")


class MentorshipRequest(Base):
    """A request by a user for mentorship with a specific mentor."""
    __tablename__ = "mentorship_requests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, accepted, rejected
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="mentorship_requests", foreign_keys=[user_id])
    mentor = relationship("User", back_populates="mentorship_assignments", foreign_keys=[mentor_id])
