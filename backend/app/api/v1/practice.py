"""
Practice Mode API Endpoints with Progress Tracking
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.practice_generator import get_practice_generator
from app.services.vector_store_service import get_vector_store
from app.services.embedding_service import get_embedding_service
from app.services.progress_service import ProgressTrackingService
from app.api.v1.dependencies import get_current_user, get_current_user_optional
from app.models.user import User
from app.db import get_db
from app.core.logging import logger


router = APIRouter(prefix="/practice", tags=["practice"])


# ── Request / Response Models ─────────────────────────────────────────────────

class GeneratePracticeRequest(BaseModel):
    topic: str
    difficulty: str = "medium"  # easy | medium | hard
    count: int = 5
    use_curriculum: bool = True  # Ground questions in CDC curriculum


class PracticeQuestion(BaseModel):
    id: int
    question: str
    answer: str
    hints: List[str]
    difficulty: str
    marks: int
    topic: str


class GeneratePracticeResponse(BaseModel):
    questions: List[PracticeQuestion]
    topic: str
    difficulty: str


class CheckAnswerRequest(BaseModel):
    user_answer: str
    correct_answer: str
    question_text: Optional[str] = None
    topic: Optional[str] = None
    chapter_code: Optional[str] = None


class CheckAnswerResponse(BaseModel):
    is_correct: bool
    feedback: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=GeneratePracticeResponse)
async def generate_practice_questions(request: GeneratePracticeRequest):
    """Generate practice questions for a given topic."""
    generator = get_practice_generator()

    # Optionally ground questions in CDC curriculum via vector search
    curriculum_context = None
    if request.use_curriculum:
        try:
            embedding_service = get_embedding_service()
            vector_store = get_vector_store()

            query_embedding = embedding_service.generate_embedding(request.topic)

            # Pull from all three content types so generated questions
            # reflect both CDC curriculum theory and real SEE exam patterns.
            # Each type searched independently — empty results are silently skipped.
            all_results = []
            if vector_store.index and vector_store.index.ntotal > 0:
                for content_type in ("curriculum", "model_question", "past_paper"):
                    hits = vector_store.search(
                        query_vector=query_embedding,
                        k=2,
                        filters={"content_type": content_type},
                    )
                    all_results.extend(hits)

            if all_results:
                curriculum_context = "\n\n".join(
                    r.get("text", "") for r in all_results if r.get("text")
                )
        except Exception as e:
            logger.warning(f"Could not fetch curriculum context: {e}")

    questions = generator.generate_questions(
        topic=request.topic,
        difficulty=request.difficulty,
        count=request.count,
        curriculum_context=curriculum_context,
    )

    if not questions:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate questions. Please try again.",
        )

    return GeneratePracticeResponse(
        questions=[PracticeQuestion(**q) for q in questions],
        topic=request.topic,
        difficulty=request.difficulty,
    )


@router.post("/check-answer", response_model=CheckAnswerResponse)
async def check_answer(
    request: CheckAnswerRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Check a student's answer and log the attempt to progress tracking
    if the user is authenticated.
    """
    generator = get_practice_generator()
    result = generator.check_answer(
        user_answer=request.user_answer,
        correct_answer=request.correct_answer,
    )
    is_correct = result.get("is_correct", False)

    if current_user:
        try:
            service = ProgressTrackingService(db)
            await service.log_interaction(
                user_id=current_user.id,
                interaction_type="practice_attempt",
                topic=request.topic,
                chapter_code=request.chapter_code,
                question_text=request.question_text,
                user_answer=request.user_answer,
                is_correct=is_correct,
                time_spent_seconds=None,
            )
            logger.info(
                f"Practice attempt logged — user={current_user.id} "
                f"topic={request.topic} correct={is_correct}"
            )
        except Exception as e:
            logger.warning(f"Failed to log practice attempt: {e}")
    else:
        logger.info("Practice attempt not logged — user not authenticated")

    return CheckAnswerResponse(**result)


@router.get("/topics")
async def get_available_topics(db: AsyncSession = Depends(get_db)):
    """
    Return all CDC Grade 10 chapters from the curriculum_nodes database.
    This endpoint derives its data from the same source as progress tracking,
    ensuring both are always in sync — no hardcoded list.
    """
    service = ProgressTrackingService(db)
    chapters = await service._get_chapters_from_db()

    topics = [
        {
            "id":           ch["name"],
            "name":         ch["name"],
            "chapter_code": ch["code"],
            "chapter_num":  ch["order"],
            "unit":         ch["unit"],
        }
        for ch in chapters
    ]

    return {"topics": topics}


@router.get("/recommendations")
async def get_practice_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return personalised practice recommendations based on weak areas
    and overall progress stats.
    """
    service = ProgressTrackingService(db)

    weak_areas   = await service.get_weak_areas(current_user.id, threshold=60.0)
    overall      = await service.get_overall_stats(current_user.id)
    see_readiness = await service.calculate_see_readiness(current_user.id)

    recommended = [
        {
            "topic":        topic.topic,
            "mastery":      topic.mastery_percentage,
            "status":       topic.mastery_level,
            "status_emoji": topic.status_emoji,
            "reason":       f"Mastery is {topic.mastery_percentage:.0f}% — needs more practice.",
        }
        for topic in weak_areas[:3]
    ]

    return {
        "recommended_topics": recommended,
        "quick_stats": {
            "see_readiness":    see_readiness["readiness_percentage"],
            "total_questions":  overall["total_questions"],
            "topics_studied":   overall["total_topics_studied"],
            "mastered_topics":  overall["mastered_topics"],
        },
    }