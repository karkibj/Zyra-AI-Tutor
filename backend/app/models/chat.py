"""
Chat History Models
Separated from chat_history.py router to avoid circular imports with db.py
"""
import uuid
from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.sql import func

from app.models.base import Base


class ChatConversation(Base):
    """Stores chat conversations for history"""
    __tablename__ = "chat_conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False)
    session_id = Column(String(36), nullable=False, unique=True)
    title = Column(String(200))
    last_message = Column(Text)
    message_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ChatMessage(Base):
    """Stores individual messages in conversations"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String(36), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'tutor'
    content = Column(Text, nullable=False)
    metadata_json = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())