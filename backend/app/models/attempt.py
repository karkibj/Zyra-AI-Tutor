from sqlalchemy import Column, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .base import Base

class Attempt(Base):
    __tablename__ = "attempts"

    attempt_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.question_id"), nullable=False)

    is_correct = Column(Boolean, default=False)
    time_spent_ms = Column(Integer, default=0)
    hint_level_used = Column(Integer, default=0)

    attempt_at = Column(DateTime, default=datetime.utcnow)
