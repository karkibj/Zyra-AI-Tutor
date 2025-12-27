from sqlalchemy import Column, Boolean, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class Attempt(Base):
    """Attempt model for tracking student question attempts"""
    __tablename__ = "attempts"

    attempt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False)
    is_correct = Column(Boolean, nullable=True)
    time_spent_ms = Column(Integer, nullable=True)
    hint_level_used = Column(Integer, nullable=True)
    attempt_at = Column(TIMESTAMP(timezone=False), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")

    def __repr__(self):
        return f"<Attempt(attempt_id={self.attempt_id}, user_id={self.user_id}, is_correct={self.is_correct})>"