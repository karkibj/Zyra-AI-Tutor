from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class ChatSession(Base):
    """Chat session model for conversation tracking"""
    __tablename__ = "chat_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.chapter_id"), nullable=True)
    started_at = Column(TIMESTAMP(timezone=False), server_default=func.now())
    ended_at = Column(TIMESTAMP(timezone=False), nullable=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    chapter = relationship("Chapter", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(session_id={self.session_id}, user_id={self.user_id}, started_at={self.started_at})>"