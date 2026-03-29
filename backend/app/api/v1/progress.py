"""
Enhanced Progress Tracking API - FINAL VERSION
Works with your existing curriculum_nodes and TopicMastery @property decorators
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.db import get_db
from app.api.v1.dependencies import get_current_user
from app.models.user import User
from app.services.progress_service import ProgressTrackingService


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class OverallStatsResponse(BaseModel):
    overall_mastery: float
    total_questions: int
    correct_answers: int
    total_topics_studied: int
    mastered_topics: int


class TopicProgressResponse(BaseModel):
    topic: str
    chapter_code: str | None
    total_questions_attempted: int
    correct_answers: int
    mastery_percentage: float
    mastery_level: str
    status_emoji: str
    last_practiced_at: str | None


class ChapterProgressResponse(BaseModel):
    chapter_id: int
    chapter_name: str
    chapter_code: str
    unit: str
    testing_area: str
    see_marks: int
    mastery_percentage: float
    total_questions: int
    correct_answers: int
    mastery_level: str
    status_emoji: str
    last_practiced_at: str | None
    topics_practiced: List[str]


class TestingAreaResponse(BaseModel):
    testing_area: str
    see_marks: int
    chapters: List[str]
    mastery_percentage: float
    total_questions: int
    correct_answers: int
    chapter_count: int


class DailyActivityResponse(BaseModel):
    date: str
    day_name: str
    questions: int
    accuracy: float


class RecentActivityResponse(BaseModel):
    today: int
    this_week: int
    this_month: int
    week_accuracy: float


class SEEReadinessResponse(BaseModel):
    readiness_percentage: float
    projected_marks: float
    total_marks: int
    testing_areas: List[TestingAreaResponse]


class CompleteDashboardResponse(BaseModel):
    overall_stats: OverallStatsResponse
    topic_progress: List[TopicProgressResponse]
    weak_areas: List[TopicProgressResponse]
    recent_activity: RecentActivityResponse
    chapters_progress: List[ChapterProgressResponse]
    testing_areas: List[TestingAreaResponse]
    see_readiness: SEEReadinessResponse
    daily_activity: List[DailyActivityResponse]


# ============================================================================
# ROUTER
# ============================================================================

router = APIRouter(prefix="/progress", tags=["Progress Tracking"])


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=CompleteDashboardResponse)
async def get_complete_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete progress dashboard with all analytics
    
    Includes:
    - Overall statistics
    - Topic-wise progress
    - Weak areas
    - Recent activity
    - All CDC chapters from curriculum_nodes
    - SEE testing areas breakdown
    - SEE readiness calculation
    - Daily activity (7 days)
    """
    service = ProgressTrackingService(db)
    
    # Fetch all data
    overall_stats = await service.get_overall_stats(current_user.id)
    topic_progress = await service.get_topic_progress_breakdown(current_user.id)
    weak_areas_data = await service.get_weak_areas(current_user.id, threshold=50.0)
    recent_activity = await service.get_recent_activity(current_user.id)
    chapters_progress = await service.get_all_chapters_progress(current_user.id)
    testing_areas = await service.get_testing_areas_breakdown(current_user.id)
    see_readiness = await service.calculate_see_readiness(current_user.id)
    daily_activity = await service.get_daily_activity(current_user.id, days=7)
    
    # Format weak areas (TopicMastery uses @property, not DB columns)
    weak_areas = [
        {
            'topic': m.topic,
            'chapter_code': m.chapter_code,
            'total_questions_attempted': m.total_questions_attempted,
            'correct_answers': m.correct_answers,
            'mastery_percentage': round(m.mastery_percentage, 2),
            'mastery_level': m.mastery_level,  # @property
            'status_emoji': m.status_emoji,    # @property
            'last_practiced_at': m.last_practiced_at.isoformat() if m.last_practiced_at else None
        }
        for m in weak_areas_data
    ]
    
    return {
        "overall_stats": overall_stats,
        "topic_progress": topic_progress,
        "weak_areas": weak_areas,
        "recent_activity": recent_activity,
        "chapters_progress": chapters_progress,
        "testing_areas": testing_areas,
        "see_readiness": see_readiness,
        "daily_activity": daily_activity
    }


@router.get("/chapters", response_model=List[ChapterProgressResponse])
async def get_all_chapters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress for all CDC chapters from curriculum_nodes
    Includes both practiced and unpracticed chapters
    """
    service = ProgressTrackingService(db)
    return await service.get_all_chapters_progress(current_user.id)


@router.get("/testing-areas", response_model=List[TestingAreaResponse])
async def get_testing_areas(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get mastery breakdown by SEE testing areas
    """
    service = ProgressTrackingService(db)
    return await service.get_testing_areas_breakdown(current_user.id)


@router.get("/see-readiness", response_model=SEEReadinessResponse)
async def get_see_readiness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate SEE exam readiness score
    Weighted by marks allocation
    """
    service = ProgressTrackingService(db)
    return await service.calculate_see_readiness(current_user.id)


@router.get("/daily-activity", response_model=List[DailyActivityResponse])
async def get_daily_activity(
    days: int = Query(7, ge=1, le=30, description="Number of days"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get daily activity breakdown
    """
    service = ProgressTrackingService(db)
    return await service.get_daily_activity(current_user.id, days=days)


@router.get("/topics", response_model=List[TopicProgressResponse])
async def get_topic_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed progress for all topics practiced
    """
    service = ProgressTrackingService(db)
    return await service.get_topic_progress_breakdown(current_user.id)


@router.get("/weak-areas", response_model=List[TopicProgressResponse])
async def get_weak_areas(
    threshold: float = Query(50.0, ge=0.0, le=100.0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get topics below mastery threshold
    """
    service = ProgressTrackingService(db)
    weak_areas_data = await service.get_weak_areas(current_user.id, threshold=threshold)
    
    return [
        {
            'topic': m.topic,
            'chapter_code': m.chapter_code,
            'total_questions_attempted': m.total_questions_attempted,
            'correct_answers': m.correct_answers,
            'mastery_percentage': round(m.mastery_percentage, 2),
            'mastery_level': m.mastery_level,  # @property
            'status_emoji': m.status_emoji,    # @property
            'last_practiced_at': m.last_practiced_at.isoformat() if m.last_practiced_at else None
        }
        for m in weak_areas_data
    ]


@router.get("/activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent activity summary
    """
    service = ProgressTrackingService(db)
    return await service.get_recent_activity(current_user.id, days=days)


@router.get("/overall", response_model=OverallStatsResponse)
async def get_overall_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall statistics only
    """
    service = ProgressTrackingService(db)
    return await service.get_overall_stats(current_user.id)


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "progress_tracking",
        "integration": "curriculum_nodes",
        "features": [
            "overall_stats",
            "topic_progress",
            "chapter_progress_from_db",
            "testing_areas",
            "see_readiness",
            "daily_activity",
            "weak_areas",
            "quick_stats"  # ✅ NEW!
        ]
    }


@router.get("/quick-stats")
async def get_quick_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Lightweight stats for home page preview
    Fast alternative to full /dashboard endpoint
    """
    service = ProgressTrackingService(db)
    
    # Get essential data only
    overall = await service.get_overall_stats(current_user.id)
    see_readiness = await service.calculate_see_readiness(current_user.id)
    weak_areas_data = await service.get_weak_areas(current_user.id, threshold=60.0)
    topic_progress = await service.get_topic_progress_breakdown(current_user.id)
    
    # Find last practiced topic — topic_progress returns dicts
    last_topic = None
    if topic_progress:
        sorted_topics = sorted(
            topic_progress,
            key=lambda x: x.get('last_practiced_at') or '' if isinstance(x, dict) else (x.last_practiced_at or ''),
            reverse=True
        )
        if sorted_topics:
            lt = sorted_topics[0]
            if isinstance(lt, dict):
                last_topic = {
                    "topic": lt['topic'],
                    "mastery": lt['mastery_percentage'],
                    "status_emoji": lt['status_emoji']
                }
            else:
                last_topic = {
                    "topic": lt.topic,
                    "mastery": lt.mastery_percentage,
                    "status_emoji": lt.status_emoji
                }
    
    return {
        "see_readiness": see_readiness['readiness_percentage'],
        "projected_marks": see_readiness['projected_marks'],
        "questions_practiced": overall['total_questions'],
        "topics_studied": overall['total_topics_studied'],
        "last_topic": last_topic,
        "weak_count": len(weak_areas_data)
    }


@router.get("/recommendations")
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get smart practice recommendations
    
    Returns:
    - Top 3 weak areas sorted by SEE marks impact
    - Mastered topics for celebration
    - Continue learning (last practiced topic)
    - Predictions (questions needed to next level)
    """
    service = ProgressTrackingService(db)
    
    # Get weak areas (below 75% mastery)
    weak_areas_data = await service.get_weak_areas(current_user.id, threshold=75.0)
    
    # Get all topics to find mastered ones
    all_topics = await service.get_topic_progress_breakdown(current_user.id)
    
    # Get testing areas for marks impact
    testing_areas = await service.get_testing_areas_breakdown(current_user.id)
    
    # Create marks lookup (topic -> marks)
    topic_marks = {}
    for area in testing_areas:
        # Handle dict response
        area_marks = area['see_marks'] if isinstance(area, dict) else area.see_marks
        area_chapters = area['chapters'] if isinstance(area, dict) else area.chapters
        area_count = area['chapter_count'] if isinstance(area, dict) else area.chapter_count
        
        # Simplified: assign marks to each chapter
        for chapter in area_chapters:
            topic_marks[chapter.lower()] = area_marks
    
    # Format weak areas with predictions
    recommended = []
    for topic_data in weak_areas_data[:5]:  # Top 5 weak areas
        # Handle dict or object
        if isinstance(topic_data, dict):
            topic_name = topic_data['topic']
            mastery = topic_data['mastery_percentage']
            emoji = topic_data['status_emoji']
            level = topic_data['mastery_level']
            attempted = topic_data['total_questions_attempted']
            correct = topic_data['correct_answers']
        else:
            topic_name = topic_data.topic
            mastery = topic_data.mastery_percentage
            emoji = topic_data.status_emoji
            level = topic_data.mastery_level
            attempted = topic_data.total_questions_attempted
            correct = topic_data.correct_answers
        
        # Find marks impact
        marks_impact = 0
        for topic_key, marks in topic_marks.items():
            if topic_key in topic_name.lower():
                marks_impact = marks
                break
        
        # Calculate questions needed to next mastery level
        next_threshold = 51 if mastery < 51 else (76 if mastery < 76 else 90)
        
        # Estimate questions needed
        if attempted > 0:
            accuracy = correct / attempted
            if accuracy > 0:
                questions_needed = max(1, int((next_threshold - mastery) / (accuracy * 10)))
            else:
                questions_needed = 5
        else:
            questions_needed = 3
        
        recommended.append({
            "topic": topic_name,
            "mastery": round(mastery, 1),
            "status_emoji": emoji,
            "mastery_level": level,
            "marks_impact": marks_impact,
            "questions_needed": min(questions_needed, 10),
            "next_threshold": next_threshold,
            "reason": f"Practice {questions_needed} more questions to reach {next_threshold}% mastery!"
        })
    
    # Sort by marks impact (highest first)
    recommended.sort(key=lambda x: x['marks_impact'], reverse=True)
    
    # Find mastered topics (>= 76%) — always use dict access since service returns dicts
    mastered = []
    for topic_data in all_topics:
        if isinstance(topic_data, dict):
            pct = topic_data.get('mastery_percentage', 0)
            if pct >= 76:
                mastered.append({
                    "topic": topic_data['topic'],
                    "mastery": round(pct, 1),
                    "status_emoji": topic_data.get('status_emoji', '✅')
                })
        else:
            pct = topic_data.mastery_percentage
            if pct >= 76:
                mastered.append({
                    "topic": topic_data.topic,
                    "mastery": round(pct, 1),
                    "status_emoji": topic_data.status_emoji
                })
    
    # Find last practiced (continue learning) — service returns dicts
    continue_learning = None
    if all_topics:
        def get_last_practiced(t):
            if isinstance(t, dict):
                return t.get('last_practiced_at') or ''
            return (t.last_practiced_at.isoformat() if t.last_practiced_at else '') or ''
        
        sorted_topics = sorted(all_topics, key=get_last_practiced, reverse=True)
        
        if sorted_topics:
            lt = sorted_topics[0]
            last_practiced = get_last_practiced(lt)
            
            if last_practiced:
                if isinstance(lt, dict):
                    continue_learning = {
                        "topic": lt.get('topic', ''),
                        "mastery": round(lt.get('mastery_percentage', 0), 1),
                        "status_emoji": lt.get('status_emoji', '⚪'),
                        "last_practiced": last_practiced
                    }
                else:
                    continue_learning = {
                        "topic": lt.topic,
                        "mastery": round(lt.mastery_percentage, 1),
                        "status_emoji": lt.status_emoji,
                        "last_practiced": lt.last_practiced_at.isoformat() if lt.last_practiced_at else None
                    }
    
    return {
        "recommended": recommended[:3],  # Top 3
        "mastered": mastered,
        "continue_learning": continue_learning,
        "total_weak_areas": len(weak_areas_data)
    }


@router.get("/predictions")
async def get_predictions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress predictions and milestones
    
    Returns predictions like:
    - "Practice X more questions in Y to reach Z%"
    - "Master Topic A to gain +X marks"
    - "You're Y% away from SEE ready"
    """
    service = ProgressTrackingService(db)
    
    # Get current readiness
    see_readiness = await service.calculate_see_readiness(current_user.id)
    current_readiness = see_readiness['readiness_percentage']
    
    # Get weak areas
    weak_areas_data = await service.get_weak_areas(current_user.id, threshold=75.0)
    
    # Get testing areas
    testing_areas = await service.get_testing_areas_breakdown(current_user.id)
    
    predictions = []
    
    # Prediction 1: SEE Readiness gap
    if current_readiness < 75:
        gap = 75 - current_readiness
        predictions.append({
            "type": "see_readiness",
            "message": f"You're {gap:.0f}% away from SEE ready (75% target)",
            "icon": "🎯",
            "priority": "high"
        })
    
    # Prediction 2: Biggest impact topics
    if weak_areas_data and testing_areas:
        topic_impacts = []
        
        for topic_data in weak_areas_data[:3]:
            # Handle dict or object
            if isinstance(topic_data, dict):
                topic_name = topic_data['topic']
                topic_mastery = topic_data['mastery_percentage']
            else:
                topic_name = topic_data.topic
                topic_mastery = topic_data.mastery_percentage
            
            for area in testing_areas:
                # Handle dict or object
                if isinstance(area, dict):
                    area_chapters = area['chapters']
                    area_marks = area['see_marks']
                else:
                    area_chapters = area.chapters
                    area_marks = area.see_marks
                
                if any(chapter.lower() in topic_name.lower() for chapter in area_chapters):
                    impact = area_marks * (76 - topic_mastery) / 100
                    topic_impacts.append({
                        "topic": topic_name,
                        "marks_gain": impact,
                        "current_mastery": topic_mastery
                    })
                    break
        
        if topic_impacts:
            best = max(topic_impacts, key=lambda x: x['marks_gain'])
            predictions.append({
                "type": "biggest_impact",
                "message": f"Master {best['topic']} to gain +{best['marks_gain']:.1f} marks",
                "icon": "📈",
                "priority": "high"
            })
    
    # Prediction 3: Quick wins (close to next level)
    quick_wins = []
    for topic_data in weak_areas_data:
        # Handle dict or object
        if isinstance(topic_data, dict):
            mastery = topic_data['mastery_percentage']
            topic_name = topic_data['topic']
        else:
            mastery = topic_data.mastery_percentage
            topic_name = topic_data.topic
        
        if 45 <= mastery < 51 or 65 <= mastery < 76:
            quick_wins.append((topic_name, mastery))
    
    if quick_wins:
        topic_name, mastery = quick_wins[0]
        next_level = 51 if mastery < 51 else 76
        gap = next_level - mastery
        predictions.append({
            "type": "quick_win",
            "message": f"Just {gap:.0f}% more to level up {topic_name}!",
            "icon": "⚡",
            "priority": "medium"
        })
    
    return {
        "predictions": predictions,
        "see_readiness_current": round(current_readiness, 1),
        "see_readiness_target": 75.0,
        "gap_to_target": max(0, round(75 - current_readiness, 1))
    }


@router.get("/streak")
async def get_study_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate study streak (consecutive days practicing)
    """
    service = ProgressTrackingService(db)
    
    # Get last 30 days of activity
    daily_activity = await service.get_daily_activity(current_user.id, days=30)
    
    # Calculate current streak
    # daily_activity is ordered newest->oldest; skip today if 0 (student may not have practiced yet today)
    current_streak = 0
    start_idx = 0
    if daily_activity:
        first = daily_activity[0]
        first_q = first['questions'] if isinstance(first, dict) else first.questions
        if first_q == 0:
            start_idx = 1  # Start from yesterday if today has no activity yet
    
    for day in daily_activity[start_idx:]:
        questions = day['questions'] if isinstance(day, dict) else day.questions
        if questions > 0:
            current_streak += 1
        else:
            break  # Streak broken
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    for day in daily_activity:
        questions = day['questions'] if isinstance(day, dict) else day.questions
        if questions > 0:
            temp_streak += 1
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0
    
    # Get last practice date
    last_practice = None
    if daily_activity:
        first_day = daily_activity[0]
        questions = first_day['questions'] if isinstance(first_day, dict) else first_day.questions
        if questions > 0:
            last_practice = first_day['date'] if isinstance(first_day, dict) else first_day.date
    
    # Check if active today
    is_active = False
    if daily_activity:
        first_day = daily_activity[0]
        questions = first_day['questions'] if isinstance(first_day, dict) else first_day.questions
        is_active = questions > 0
    
    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "last_practice_date": last_practice,
        "is_active_today": is_active
    }