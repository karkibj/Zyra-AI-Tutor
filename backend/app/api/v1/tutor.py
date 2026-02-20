"""
Tutor API - Student Q&A endpoints
Uses LangGraph multi-agent workflow
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db import get_db
from app.services.langgraph_rag_service import get_langgraph_rag_service

router = APIRouter(prefix="/tutor", tags=["Tutor"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AskRequest(BaseModel):
    question: str
    chapter_code: Optional[str] = None
    session_id: Optional[str] = None


class AskResponse(BaseModel):
    answer: str
    intent: str
    sources: List[Dict]
    session_id: str
    chunk_count: int
    response_time: float
    metadata: Optional[Dict[str, Any]] = None


class StatsResponse(BaseModel):
    workflow: str
    vector_store: Dict[str, Any]
    embedding_model: str
    llm_model: str
    agents: List[str]
    active_sessions: int


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/ask", response_model=AskResponse)
async def ask_question(
    request: AskRequest,
    db: AsyncSession = Depends(get_db)  # Keep for future use
):
    """
    Ask a question to Zyra tutor
    
    Uses LangGraph multi-agent workflow:
    - Intent Router: Classifies question type
    - Retriever: Gets relevant context from vector store
    - Curriculum Agent: Checks educational context
    - Tutor Agent: Explains concept clearly
    - Example Agent: Provides worked examples
    - Practice Suggester: Offers practice questions
    - Response Compiler: Builds final answer
    
    Example:
```json
    {
        "question": "What is compound interest?",
        "chapter_code": "CDC-10-MATH-CH02",
        "session_id": "optional-uuid-here"
    }
```
    """
    rag_service = get_langgraph_rag_service()
    
    # Ask question through LangGraph workflow
    # Note: Our RAG service uses in-memory conversation history
    try:
        result = await rag_service.ask(
            question=request.question,
            chapter_filter=request.chapter_code,
            session_id=request.session_id,
            conversation_history=None  # RAG service manages this internally
        )
        
        return AskResponse(**result)
        
    except Exception as e:
        print(f"❌ Error in ask_question: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {str(e)}"
        )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get RAG system statistics
    
    Returns information about:
    - Active workflow
    - Vector store status
    - Models being used
    - Available agents
    """
    rag_service = get_langgraph_rag_service()
    stats = rag_service.get_stats()
    return StatsResponse(**stats)


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Status of tutor service and dependencies
    """
    try:
        rag_service = get_langgraph_rag_service()
        stats = rag_service.get_stats()
        
        return {
            "status": "healthy",
            "service": "tutor",
            "workflow": "langgraph_multi_agent",
            "vector_store_vectors": stats.get("vector_store", {}).get("total_vectors", 0),
            "agents_active": len(stats.get("agents", []))
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )