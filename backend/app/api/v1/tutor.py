from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from app.services.tutor_service import tutor_service

router = APIRouter(prefix="/tutor", tags=["AI Tutor"])


class TutorQuery(BaseModel):
    query: str = Field(..., description="Student's question")
    chapter: Optional[str] = Field(None, description="Chapter context (e.g., 'money_exchange')")
    conversation_history: Optional[List[Dict]] = Field(None, description="Previous messages")


class TutorResponse(BaseModel):
    reply: str
    intent: str
    used_rag: bool
    sources: Optional[List[Dict]] = None


@router.post("/ask", response_model=TutorResponse)
async def ask_tutor(payload: TutorQuery):
    """
    Main endpoint for student queries.
    
    - **query**: The student's question
    - **chapter**: Optional chapter filter (e.g., "money_exchange", "sets", "geometry")
    - **conversation_history**: Optional previous messages for context
    """
    try:
        result = tutor_service.ask_question(
            query=payload.query,
            chapter=payload.chapter,
            conversation_history=payload.conversation_history
        )
        
        return TutorResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )