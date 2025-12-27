"""
Chat Service - Async CRUD operations for chat sessions and messages
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid

from app.models.chat_session import ChatSession
from app.models.chat_message import ChatMessage


class ChatService:
    """Service for managing chat sessions and messages"""

    # ==================== CHAT SESSIONS ====================

    @staticmethod
    async def create_session(
        db: AsyncSession,
        user_id: uuid.UUID,
        chapter_id: Optional[uuid.UUID] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(
            session_id=uuid.uuid4(),
            user_id=user_id,
            chapter_id=chapter_id,
            started_at=datetime.utcnow()
        )
        
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: uuid.UUID) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        stmt = select(ChatSession).where(ChatSession.session_id == session_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_with_messages(db: AsyncSession, session_id: uuid.UUID) -> Optional[ChatSession]:
        """Get a chat session with all its messages loaded"""
        stmt = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.session_id == session_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_user_sessions(
        db: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0
    ) -> List[ChatSession]:
        """List all sessions for a user, ordered by most recent"""
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def end_session(db: AsyncSession, session_id: uuid.UUID) -> Optional[ChatSession]:
        """Mark a session as ended"""
        stmt = (
            update(ChatSession)
            .where(ChatSession.session_id == session_id)
            .values(ended_at=datetime.utcnow())
            .returning(ChatSession)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> bool:
        """Delete a chat session (cascades to messages)"""
        stmt = delete(ChatSession).where(ChatSession.session_id == session_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    # ==================== CHAT MESSAGES ====================

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: uuid.UUID,
        sender: str,  # 'user' or 'assistant'
        content: str
    ) -> ChatMessage:
        """Add a message to a chat session"""
        message = ChatMessage(
            message_id=uuid.uuid4(),
            session_id=session_id,
            sender=sender,
            content=content,
            created_at=datetime.utcnow()
        )
        
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_message(db: AsyncSession, message_id: uuid.UUID) -> Optional[ChatMessage]:
        """Get a message by ID"""
        stmt = select(ChatMessage).where(ChatMessage.message_id == message_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_session_messages(
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """Get all messages for a session, ordered chronologically"""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_recent_messages(
        db: AsyncSession,
        session_id: uuid.UUID,
        n: int = 10
    ) -> List[ChatMessage]:
        """Get the N most recent messages for a session"""
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(n)
        )
        
        result = await db.execute(stmt)
        messages = list(result.scalars().all())
        
        # Return in chronological order (oldest to newest)
        return list(reversed(messages))

    @staticmethod
    async def delete_message(db: AsyncSession, message_id: uuid.UUID) -> bool:
        """Delete a message"""
        stmt = delete(ChatMessage).where(ChatMessage.message_id == message_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def delete_session_messages(db: AsyncSession, session_id: uuid.UUID) -> int:
        """Delete all messages for a session"""
        stmt = delete(ChatMessage).where(ChatMessage.session_id == session_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def count_session_messages(db: AsyncSession, session_id: uuid.UUID) -> int:
        """Count messages in a session"""
        from sqlalchemy import func
        
        stmt = (
            select(func.count(ChatMessage.message_id))
            .where(ChatMessage.session_id == session_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one()