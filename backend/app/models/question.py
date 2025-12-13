from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .base import Base

class Question(Base):
    __tablename__ = "questions"

    question_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.chapter_id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False)

    stem = Column(String, nullable=False)          # question text
    answer = Column(String, nullable=True)         # or JSON
    difficulty = Column(String, default="easy")    # easy, medium, hard
    source = Column(String, default="manual")      # manual, ai_generated, past_paper

    created_at = Column(DateTime, default=datetime.utcnow)
