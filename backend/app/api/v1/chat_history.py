"""
Chat History API - Save and retrieve conversations
Allows students to continue previous conversations
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import json

from app.db import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.models.chat import ChatConversation, ChatMessage  # ✅ Moved to models/chat.py


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SaveMessageRequest(BaseModel):
    session_id: str
    role: str  # 'user' or 'tutor'
    content: str
    metadata: Optional[dict] = None


class ConversationListItem(BaseModel):
    id: str
    session_id: str
    title: str
    last_message: str
    message_count: int
    updated_at: str


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    metadata: Optional[dict] = None
    created_at: str


class ConversationDetail(BaseModel):
    id: str
    session_id: str
    title: str
    messages: List[MessageItem]
    created_at: str
    updated_at: str


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/chat-history", tags=["Chat History"])


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/save-message")
async def save_message(
    request: SaveMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Save a chat message (user or tutor response)
    Creates conversation if it doesn't exist
    """
    # Check if conversation exists
    result = await db.execute(
        select(ChatConversation).where(
            ChatConversation.session_id == request.session_id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        # Create new conversation
        # Generate title from first user message
        title = request.content[:50] + "..." if len(request.content) > 50 else request.content
        if request.role == 'user':
            # Clean title - remove special chars, make it readable
            title = title.replace('#', '').replace('*', '').strip()
        
        conversation = ChatConversation(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            session_id=request.session_id,
            title=title,
            last_message=request.content[:100],
            message_count=0
        )
        db.add(conversation)
        await db.flush()
    
    # Save the message
    message = ChatMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation.id,
        role=request.role,
        content=request.content,
        metadata_json=json.dumps(request.metadata) if request.metadata else None
    )
    db.add(message)
    
    # Update conversation
    conversation.last_message = request.content[:100]
    conversation.message_count = conversation.message_count + 1
    conversation.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {
        "status": "saved",
        "conversation_id": conversation.id,
        "message_id": message.id
    }


@router.get("/conversations", response_model=List[ConversationListItem])
async def get_conversations(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's recent conversations for sidebar
    """
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.user_id == current_user.id)
        .order_by(desc(ChatConversation.updated_at))
        .limit(limit)
    )
    conversations = result.scalars().all()
    
    return [
        {
            "id": conv.id,
            "session_id": conv.session_id,
            "title": conv.title or "New Chat",
            "last_message": conv.last_message or "",
            "message_count": conv.message_count,
            "updated_at": conv.updated_at.isoformat()
        }
        for conv in conversations
    ]


@router.get("/conversation/{session_id}", response_model=ConversationDetail)
async def get_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full conversation with all messages
    """
    # Get conversation
    result = await db.execute(
        select(ChatConversation).where(
            ChatConversation.session_id == session_id,
            ChatConversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get all messages
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    
    return {
        "id": conversation.id,
        "session_id": conversation.session_id,
        "title": conversation.title,
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "metadata": json.loads(msg.metadata_json) if msg.metadata_json else None,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ],
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat()
    }


@router.delete("/conversation/{session_id}")
async def delete_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a conversation and all its messages
    """
    # Get conversation
    result = await db.execute(
        select(ChatConversation).where(
            ChatConversation.session_id == session_id,
            ChatConversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete all messages in this conversation first
    msgs_result = await db.execute(
        select(ChatMessage).where(ChatMessage.conversation_id == conversation.id)
    )
    messages = msgs_result.scalars().all()
    for msg in messages:
        await db.delete(msg)

    # Delete the conversation itself
    await db.delete(conversation)
    await db.commit()
    
    return {"status": "deleted", "session_id": session_id}


@router.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "chat_history",
        "features": ["save_message", "get_conversations", "get_conversation", "delete_conversation"]
    }