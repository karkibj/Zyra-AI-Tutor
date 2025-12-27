from sqlalchemy import Column, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class Question(Base):
    """Question model for practice questions"""
    __tablename__ = "questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.chapter_id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False)
    stem = Column(String, nullable=False)  # The question text
    answer = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)  # easy, medium, hard
    source = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now())

    # Relationships
    chapter = relationship("Chapter", back_populates="questions")
    subject = relationship("Subject", back_populates="questions")
    attempts = relationship("Attempt", back_populates="question")

    def __repr__(self):
        return f"<Question(question_id={self.question_id}, difficulty={self.difficulty})>"