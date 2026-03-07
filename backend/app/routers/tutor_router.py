"""
Tutor Router - Database-integrated RAG endpoints
"""
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid

from app.db import get_db
from app.rag.document_processor import DocumentProcessor
from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.integrated_rag_service import IntegratedRAGService
from pydantic import BaseModel


router = APIRouter(prefix="/api/v1/tutor", tags=["tutor"])

# Global RAG service instance
rag_service = IntegratedRAGService()


# Pydantic models for request/response
class AskRequest(BaseModel):
    question: str
    chapter_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: str


class AskResponse(BaseModel):
    answer: str
    intent: str
    sources: list
    session_id: str
    chunk_count: int
    response_time: float
    timestamp: str


class UploadResponse(BaseModel):
    document_id: str
    title: str
    chunk_count: int
    total_tokens: int
    embeddings_created: int
    status: str


# ==================== ENDPOINTS ====================

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chapter_id: str = Form(...),
    subject_id: str = Form(...),
    user_id: str = Form(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a PDF document
    
    1. Uploads PDF
    2. Extracts text
    3. Chunks content
    4. Stores in database
    5. Generates embeddings
    6. Updates FAISS index
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        file_content = await file.read()
        
        # Process document
        doc_result = await DocumentProcessor.process_document(
            db=db,
            file_content=file_content,
            filename=file.filename,
            chapter_id=uuid.UUID(chapter_id),
            subject_id=uuid.UUID(subject_id),
            uploaded_by=uuid.UUID(user_id),
            title=title,
            description=description
        )
        
        # Generate embeddings
        emb_result = await EmbeddingGenerator.create_embeddings_for_document(
            db=db,
            document_id=uuid.UUID(doc_result["document_id"])
        )
        
        # Rebuild FAISS index
        await rag_service.initialize_index(db)
        
        return {
            **doc_result,
            "embeddings_created": emb_result["embeddings_created"]
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Ask a question and get an AI-generated answer
    
    1. Classifies intent
    2. Retrieves relevant content (if needed)
    3. Generates answer
    4. Saves conversation history
    """
    try:
        # Parse UUIDs
        user_id = uuid.UUID(request.user_id)
        chapter_id = uuid.UUID(request.chapter_id) if request.chapter_id else None
        session_id = uuid.UUID(request.session_id) if request.session_id else None
        
        # Get conversation history if session exists
        conversation_history = None
        if session_id:
            conversation_history = await rag_service.get_conversation_history(
                db, session_id, limit=10
            )
        
        # Get answer
        result = await rag_service.ask(
            db=db,
            user_id=user_id,
            question=request.question,
            chapter_id=chapter_id,
            session_id=session_id,
            conversation_history=conversation_history
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question processing failed: {str(e)}")


@router.get("/initialize")
async def initialize_rag(
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize RAG system (build FAISS index from database)
    Call this on startup or after bulk document uploads
    """
    try:
        result = await rag_service.initialize_index(db)
        return {
            "status": "initialized",
            **result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Initialization failed: {str(e)}")


@router.get("/stats")
async def get_stats():
    """Get RAG system statistics"""
    return rag_service.get_stats()


@router.get("/session/{session_id}/history")
async def get_session_history(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get conversation history for a session"""
    try:
        history = await rag_service.get_conversation_history(
            db, uuid.UUID(session_id), limit=50
        )
        return {"session_id": session_id, "history": history}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")