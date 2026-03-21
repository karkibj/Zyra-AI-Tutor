"""
Tutor API - Student Q&A endpoints
Uses LangGraph multi-agent workflow + Progress Tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.db import get_db
from app.services.langgraph_rag_service import get_langgraph_rag_service
from app.api.v1.dependencies import get_current_user  # ✅ ADD THIS
from app.models.user import User  # ✅ ADD THIS

router = APIRouter(prefix="/tutor", tags=["Tutor"])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

import random

def add_encouragement_to_response(answer: str, intent: str, user_name: str) -> str:
    """
    Add encouraging phrases — language-aware (English if response is in English)
    """
    first_name = user_name.split()[0] if user_name else "Student"
    
    # Detect language from response content
    ascii_chars = sum(1 for c in answer if ord(c) < 128)
    is_english = (ascii_chars / max(len(answer), 1)) > 0.80

    if is_english:
        encouragements = [
            f"Great question, {first_name}! 💡",
            f"Well done, {first_name}! 👏",
            f"Great topic to study! 📚",
            f"You're learning well! 🌟",
        ]
        endings = [
            "\n\n💪 **You've got this!** Keep practicing!",
            "\n\n✨ **Great work!** Now try some practice questions!",
            "\n\n🎯 **Understood?** Let's solve some questions now!",
            "\n\n📝 **Master this concept!** Practice makes perfect!",
            "\n\n🚀 **Keep going!** You're getting ready for SEE!",
        ]
    else:
        encouragements = [
            f"राम्रो प्रश्न, {first_name}! 💡",
            f"धेरै राम्रो, {first_name}! 👏",
            f"शानदार प्रश्न! ✨",
            f"यो सिक्न राम्रो विषय हो! 📚",
            f"तपाईं राम्रोसँग सिक्दै हुनुहुन्छ! 🌟",
        ]
        endings = [
            "\n\n💪 **तपाईं यो गर्न सक्नुहुन्छ!** Keep practicing!",
            "\n\n✨ **राम्रो काम!** अब practice गर्नुहोस्!",
            "\n\n🎯 **बुझ्नुभयो?** अब केही questions solve गरौं!",
            "\n\n📝 **यो concept राम्रोसँग बुझ्नुहोस्!** Practice makes perfect!",
            "\n\n🚀 **अगाडि बढौं!** तपाईं SEE को लागि तयार हुँदै हुनुहुन्छ!",
        ]
    
    # Add encouragement at start (30% chance)
    if random.random() < 0.3:
        encouragement = random.choice(encouragements)
        answer = f"{encouragement}\n\n{answer}"
    
    # Add motivation at end (40% chance)
    if random.random() < 0.4:
        ending = random.choice(endings)
        answer = f"{answer}{ending}"
    
    return answer


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
    current_user: User = Depends(get_current_user),  # ✅ ADD THIS - Require authentication
    db: AsyncSession = Depends(get_db)  # Keep for future use
):
    """
    Ask a question to Zyra tutor
    
    Uses LangGraph multi-agent workflow:
    - Intent Router: Classifies question type
    - Retriever: Gets relevant context from vector store
    - Curriculum Agent: Checks educational context
    - Tutor Agent: Explains concept clearly (+ logs interaction)
    - Example Agent: Provides worked examples
    - Practice Suggester: Offers practice questions
    - Response Compiler: Builds final answer
    
    **NEW:** Automatically logs chat interactions for progress tracking
    
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
            user_id=current_user.id,  # ✅ ADD THIS - Pass user ID for progress tracking
            chapter_filter=request.chapter_code,
            session_id=request.session_id,
            conversation_history=None  # RAG service manages this internally
        )
        
        # ✅ ADD ENCOURAGEMENT - Make responses more student-friendly
        enhanced_answer = add_encouragement_to_response(
            answer=result['answer'],
            intent=result.get('intent', ''),
            user_name=current_user.full_name
        )
        result['answer'] = enhanced_answer
        
        return AskResponse(**result)
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Error in ask_question: {error_str}")
        import traceback
        traceback.print_exc()

        # Friendly message for rate limit — no 500 crash
        if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
            return AskResponse(
                answer="⚠️ Zyra is temporarily busy due to high usage. Please wait a moment and try again! 🙏",
                intent="error",
                sources=[],
                session_id=request.session_id or "error",
                chunk_count=0,
                response_time=0.0,
                metadata={"error": "rate_limit"}
            )

        raise HTTPException(
            status_code=500,
            detail=f"Error processing question: {error_str}"
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
            "agents_active": len(stats.get("agents", [])),
            "features": stats.get("features", [])  # ✅ Include new features list
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )


@router.get("/suggest-topics")
async def suggest_topics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get personalized topic suggestions for student
    Returns what to study next based on progress
    
    Perfect for home page "Continue Learning" section!
    """
    from app.services.progress_service import ProgressTrackingService
    
    progress_service = ProgressTrackingService(db)
    
    # Get student's progress
    weak_areas_data = await progress_service.get_weak_areas(current_user.id, threshold=60.0)
    topic_progress = await progress_service.get_topic_progress_breakdown(current_user.id)
    
    # Convert weak areas (TopicMastery objects) to dicts
    weak_areas = [
        {
            'topic': m.topic,
            'mastery_percentage': m.mastery_percentage,
            'last_practiced_at': m.last_practiced_at.isoformat() if m.last_practiced_at else None
        }
        for m in weak_areas_data
    ]
    
    # Find what to continue - most recently practiced non-mastered topic
    continue_topic = None
    if topic_progress:
        sorted_topics = sorted(
            [t for t in topic_progress if t.mastery_percentage < 76],
            key=lambda x: x.last_practiced_at or '',
            reverse=True
        )
        if sorted_topics:
            ct = sorted_topics[0]
            continue_topic = {
                "topic": ct.topic,
                "mastery": ct.mastery_percentage,
                "questions_practiced": ct.total_questions_attempted
            }
    
    # Recommendation logic
    if weak_areas:
        weakest = weak_areas[0]
        recommended = {
            "topic": weakest['topic'],
            "reason": f"तपाईंको यो topic मा practice चाहिन्छ - currently {weakest['mastery_percentage']:.0f}% mastery",
            "mastery": weakest['mastery_percentage'],
            "action": "strengthen_weak"
        }
    elif continue_topic:
        recommended = {
            "topic": continue_topic['topic'],
            "reason": f"अझै practice गर्नुहोस् - currently {continue_topic['mastery']:.0f}% mastery",
            "mastery": continue_topic['mastery'],
            "action": "continue_learning"
        }
    else:
        # New student - suggest popular starting topic
        recommended = {
            "topic": "Probability",
            "reason": "SEE तयारीको लागि राम्रो starting point! 🎯",
            "mastery": 0,
            "action": "start_fresh"
        }
    
    return {
        "recommended": recommended,
        "weak_topics": [
            {
                "topic": w['topic'],
                "mastery": w['mastery_percentage']
            }
            for w in weak_areas[:3]
        ],
        "continue_learning": continue_topic
    }

class SolutionRequest(BaseModel):
    question: str
    answer: str       # The full explanation already given
    topic: Optional[str] = None


class SolutionResponse(BaseModel):
    solution: str
    has_solution: bool


@router.post("/solution", response_model=SolutionResponse)
async def get_solution_only(request: SolutionRequest):
    """
    Lazy endpoint — called only when student clicks "Solution Only".
    Takes the existing answer and extracts a clean exam-style solution.
    No RAG, no vector store — just one focused Gemini call.
    """
    # Proof-based chapters don't have a solution view
    PROOF_CHAPTERS = ["Triangles", "Construction", "Circle", "Geometry"]
    if any(ch in (request.topic or "") for ch in PROOF_CHAPTERS):
        return SolutionResponse(solution="", has_solution=False)

    try:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from app.core.llm import get_llm

        llm = get_llm(temperature=0.1)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are extracting a clean exam-style solution from a math explanation.
Output ONLY this exact format — nothing else:

**Given:**
[list each given value as: - label: value]

**Formula:** [the main formula]

**Solution:**
[each calculation step on its own line using LaTeX]
[use $...$ for inline math, $$...$$ for display math]

**Answer:** ∴ [final answer in one clear sentence]

Rules:
- One equation per line
- No explanatory text — numbers and formulas only
- Keep it exactly as a student would write in their answer booklet"""),
            ("user", """Question: {question}

Full explanation:
{answer}

Extract the clean exam solution:""")
        ])

        chain = prompt | llm | StrOutputParser()
        solution = chain.invoke({
            "question": request.question,
            "answer": request.answer[:2500]
        })

        # Validate it has real content
        has_solution = "**Answer:**" in solution or "∴" in solution

        return SolutionResponse(
            solution=solution.strip() if has_solution else "",
            has_solution=has_solution
        )

    except Exception as e:
        print(f" Solution endpoint error: {e}")
        return SolutionResponse(solution="", has_solution=False)