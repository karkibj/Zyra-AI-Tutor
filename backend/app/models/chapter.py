from sqlalchemy import Column, String, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class Chapter(Base):
    """Chapter model for organizing content by topics"""
    __tablename__ = "chapters"

    chapter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False)
    name = Column(String, nullable=False)
    chapter_number = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationships
    subject = relationship("Subject", back_populates="chapters")
    documents = relationship("Document", back_populates="chapter")
    questions = relationship("Question", back_populates="chapter")
    chat_sessions = relationship("ChatSession", back_populates="chapter")

    def __repr__(self):
        return f"<Chapter(chapter_id={self.chapter_id}, name={self.name}, chapter_number={self.chapter_number})>"