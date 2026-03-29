import uuid
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.models.base import Base


class StudentInteraction(Base):
    """Tracks every student interaction (chat questions, practice attempts)"""
    __tablename__ = "student_interactions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(String(50), nullable=False)  # 'chat_question', 'practice_attempt'
    topic = Column(String(100))
    chapter_code = Column(String(50))
    question_text = Column(Text)
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    time_spent_seconds = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TopicMastery(Base):
    """Aggregated mastery data per topic per student"""
    __tablename__ = "topic_mastery"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    topic = Column(String(100), nullable=False)
    chapter_code = Column(String(50))
    total_questions_attempted = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    mastery_percentage = Column(Float, default=0.0)
    last_practiced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    @property
    def mastery_level(self) -> str:
        """Returns mastery level based on percentage"""
        if self.mastery_percentage >= 76:
            return "mastered"
        elif self.mastery_percentage >= 51:
            return "improving"
        elif self.mastery_percentage >= 26:
            return "learning"
        else:
            return "beginner"
    
    @property
    def status_emoji(self) -> str:
        """Returns emoji for mastery level"""
        level_map = {
            "mastered": "✅",
            "improving": "🟠",
            "learning": "🟡",
            "beginner": "🔴"
        }
        return level_map.get(self.mastery_level, "⚪")