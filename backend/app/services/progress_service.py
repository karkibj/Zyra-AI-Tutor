"""
Progress Tracking Service — integrated with curriculum_nodes table.
All chapter data comes from the database; no hardcoded chapter lists.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
import uuid

from app.models.progress import StudentInteraction, TopicMastery
from app.models.curriculum import CurriculumNode
from app.models.user import User
from app.core.logging import logger


# SEE marks per chapter — fixed NEB government exam specification.
# Kept here (not in the DB) because these are official exam weights, not
# curriculum content, and they change only with a policy revision.
SEE_MARKS: Dict[str, tuple] = {
    "CDC-10-MATH-CH01": (6,  "Sets"),
    "CDC-10-MATH-CH02": (5,  "Financial Mathematics"),
    "CDC-10-MATH-CH03": (4,  "Financial Mathematics"),
    "CDC-10-MATH-CH04": (4,  "Financial Mathematics"),
    "CDC-10-MATH-CH05": (8,  "Mensuration"),
    "CDC-10-MATH-CH06": (5,  "Algebra"),
    "CDC-10-MATH-CH07": (5,  "Algebra"),
    "CDC-10-MATH-CH08": (5,  "Algebra"),
    "CDC-10-MATH-CH09": (5,  "Algebra"),
    "CDC-10-MATH-CH10": (5,  "Geometry"),
    "CDC-10-MATH-CH11": (4,  "Geometry"),
    "CDC-10-MATH-CH12": (4,  "Geometry"),
    "CDC-10-MATH-CH13": (6,  "Statistics & Probability"),
    "CDC-10-MATH-CH14": (5,  "Statistics & Probability"),
    "CDC-10-MATH-CH15": (4,  "Trigonometry"),
}


def _mastery_level(pct: float) -> str:
    """Derive a mastery level label from a percentage score."""
    if pct >= 76:   return "mastered"
    if pct >= 51:   return "improving"
    if pct >= 26:   return "learning"
    if pct > 0:     return "beginner"
    return "not_started"


def _status_label(level: str) -> str:
    """
    Return a text label for a mastery level.
    Replaces the emoji strings previously used for status_emoji
    so the field stays in the API response without emoji characters.
    """
    return {
        "mastered":    "Mastered",
        "improving":   "Improving",
        "learning":    "Learning",
        "beginner":    "Beginner",
        "not_started": "Not started",
    }.get(level, "Not started")


class ProgressTrackingService:
    """
    Progress Tracking Service — all chapter data sourced from curriculum_nodes.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._chapter_cache: Optional[List[Dict[str, Any]]] = None

    # ── Interaction Logging ───────────────────────────────────────────────────

    async def log_interaction(
        self,
        user_id: str,
        interaction_type: str,
        topic: Optional[str] = None,
        chapter_code: Optional[str] = None,
        question_text: Optional[str] = None,
        user_answer: Optional[str] = None,
        is_correct: Optional[bool] = None,
        time_spent_seconds: Optional[int] = None,
    ) -> StudentInteraction:
        """Log a student interaction and update mastery accordingly."""
        interaction = StudentInteraction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            interaction_type=interaction_type,
            topic=topic,
            chapter_code=chapter_code,
            question_text=question_text,
            user_answer=user_answer,
            is_correct=is_correct,
            time_spent_seconds=time_spent_seconds,
        )

        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)

        if interaction_type == "practice_attempt" and topic and is_correct is not None:
            await self.update_topic_mastery(user_id, topic, chapter_code, is_correct)
        elif interaction_type == "chat_question" and topic:
            await self._register_chat_engagement(user_id, topic, chapter_code)

        return interaction

    async def _register_chat_engagement(
        self,
        user_id: str,
        topic: str,
        chapter_code: Optional[str] = None,
    ) -> None:
        """
        Create a zero-attempt mastery row when a student explores a topic
        through chat, so it appears in the dashboard without practice data.
        Does not overwrite existing mastery records.
        """
        result = await self.db.execute(
            select(TopicMastery).where(
                TopicMastery.user_id == user_id,
                TopicMastery.topic == topic,
            )
        )
        if result.scalar_one_or_none():
            return  # Already exists — nothing to do

        self.db.add(TopicMastery(
            id=str(uuid.uuid4()),
            user_id=user_id,
            topic=topic,
            chapter_code=chapter_code,
            total_questions_attempted=0,
            correct_answers=0,
            mastery_percentage=0.0,
            last_practiced_at=None,
        ))
        await self.db.flush()

    # ── Mastery Updates ───────────────────────────────────────────────────────

    async def update_topic_mastery(
        self,
        user_id: str,
        topic: str,
        chapter_code: Optional[str] = None,
        is_correct: bool = True,
    ) -> TopicMastery:
        """Upsert topic mastery and recalculate the mastery percentage."""
        values = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "topic": topic,
            "chapter_code": chapter_code,
            "total_questions_attempted": 1,
            "correct_answers": 1 if is_correct else 0,
            "last_practiced_at": datetime.utcnow(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        stmt = (
            pg_insert(TopicMastery)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["user_id", "topic"],
                set_={
                    "total_questions_attempted": TopicMastery.total_questions_attempted + 1,
                    "correct_answers": TopicMastery.correct_answers + (1 if is_correct else 0),
                    "last_practiced_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                },
            )
            .returning(TopicMastery)
        )

        result = await self.db.execute(stmt)
        await self.db.flush()
        mastery = result.scalar_one()

        if mastery.total_questions_attempted > 0:
            mastery.mastery_percentage = round(
                (mastery.correct_answers / mastery.total_questions_attempted) * 100, 2
            )

        await self.db.commit()
        await self.db.refresh(mastery)
        return mastery

    # ── Chapter Data ──────────────────────────────────────────────────────────

    async def _get_chapters_from_db(self) -> List[Dict[str, Any]]:
        """
        Fetch all active chapter nodes from curriculum_nodes.
        Result is cached per-request to avoid repeated queries.
        """
        if self._chapter_cache is not None:
            return self._chapter_cache

        result = await self.db.execute(
            select(CurriculumNode)
            .where(
                CurriculumNode.node_type == "chapter",
                CurriculumNode.active == True,
            )
            .order_by(CurriculumNode.order_num)
        )
        chapter_nodes = result.scalars().all()

        chapters = []
        for node in chapter_nodes:
            metadata = node.node_metadata or {}
            see_marks, testing_area = SEE_MARKS.get(
                node.code, (0, metadata.get("unit", "General"))
            )
            chapters.append({
                "id":           str(node.id),
                "code":         node.code,
                "name":         node.name,
                "description":  node.description,
                "order":        node.order_num,
                "unit":         metadata.get("unit", "Unknown"),
                "testing_area": testing_area,
                "see_marks":    see_marks,
            })

        self._chapter_cache = chapters
        return chapters

    # ── Progress Queries ──────────────────────────────────────────────────────

    async def get_all_chapters_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Return progress for every CDC chapter, merging DB chapter definitions
        with the student's topic mastery records.
        """
        chapters = await self._get_chapters_from_db()

        result = await self.db.execute(
            select(TopicMastery).where(TopicMastery.user_id == user_id)
        )
        masteries = result.scalars().all()

        chapter_progress = []
        for idx, chapter in enumerate(chapters, 1):
            matched = [
                m for m in masteries
                if (m.chapter_code and m.chapter_code == chapter["code"])
                or chapter["name"].lower() in m.topic.lower()
            ]

            total_q   = sum(m.total_questions_attempted for m in matched)
            correct   = sum(m.correct_answers for m in matched)
            mastery   = round((correct / total_q) * 100, 2) if total_q > 0 else 0.0
            level     = _mastery_level(mastery)

            last_dates = [m.last_practiced_at for m in matched if m.last_practiced_at]
            last_practiced = max(last_dates).isoformat() if last_dates else None

            chapter_progress.append({
                "chapter_id":        idx,
                "chapter_name":      chapter["name"],
                "chapter_code":      chapter["code"],
                "unit":              chapter["unit"],
                "testing_area":      chapter["testing_area"],
                "see_marks":         chapter["see_marks"],
                "mastery_percentage": mastery,
                "total_questions":   total_q,
                "correct_answers":   correct,
                "mastery_level":     level,
                "status_emoji":      _status_label(level),
                "last_practiced_at": last_practiced,
                "topics_practiced":  [m.topic for m in matched],
            })

        return chapter_progress

    async def get_overall_stats(self, user_id: str) -> Dict[str, Any]:
        """Return aggregate statistics for a student."""
        result = await self.db.execute(
            select(
                func.count(StudentInteraction.id),
                func.sum(
                    func.cast(StudentInteraction.is_correct.is_(True), Integer)
                ),
            ).where(
                StudentInteraction.user_id == user_id,
                StudentInteraction.interaction_type == "practice_attempt",
            )
        )
        total_q, correct = result.first()
        total_q, correct = total_q or 0, correct or 0

        result = await self.db.execute(
            select(TopicMastery).where(TopicMastery.user_id == user_id)
        )
        masteries = result.scalars().all()

        overall_mastery = (
            sum(m.mastery_percentage for m in masteries) / len(masteries)
            if masteries else 0.0
        )

        return {
            "overall_mastery":     round(overall_mastery, 2),
            "total_questions":     total_q,
            "correct_answers":     correct,
            "total_topics_studied": len(masteries),
            "mastered_topics":     sum(1 for m in masteries if m.mastery_percentage >= 76),
        }

    async def get_weak_areas(
        self, user_id: str, threshold: float = 50.0
    ) -> List[TopicMastery]:
        """Return topics below the mastery threshold, ordered by weakest first."""
        result = await self.db.execute(
            select(TopicMastery)
            .where(
                TopicMastery.user_id == user_id,
                TopicMastery.mastery_percentage < threshold,
            )
            .order_by(TopicMastery.mastery_percentage)
        )
        return result.scalars().all()

    async def get_topic_progress_breakdown(self, user_id: str) -> List[Dict[str, Any]]:
        """Return per-topic mastery details, ordered by mastery descending."""
        result = await self.db.execute(
            select(TopicMastery)
            .where(TopicMastery.user_id == user_id)
            .order_by(desc(TopicMastery.mastery_percentage))
        )
        return [
            {
                "topic":                    m.topic,
                "chapter_code":             m.chapter_code,
                "total_questions_attempted": m.total_questions_attempted,
                "correct_answers":          m.correct_answers,
                "mastery_percentage":       round(m.mastery_percentage, 2),
                "mastery_level":            m.mastery_level,
                "status_emoji":             _status_label(m.mastery_level),
                "last_practiced_at": (
                    m.last_practiced_at.isoformat() if m.last_practiced_at else None
                ),
            }
            for m in result.scalars().all()
        ]

    async def get_testing_areas_breakdown(self, user_id: str) -> List[Dict[str, Any]]:
        """Aggregate mastery by SEE testing area."""
        chapters_progress = await self.get_all_chapters_progress(user_id)

        areas: Dict[str, Dict[str, Any]] = {}
        for ch in chapters_progress:
            area = ch["testing_area"]
            if area not in areas:
                areas[area] = {
                    "testing_area":    area,
                    "see_marks":       0,
                    "chapters":        [],
                    "total_questions": 0,
                    "correct_answers": 0,
                    "chapter_count":   0,
                }
            areas[area]["see_marks"]       += ch["see_marks"]
            areas[area]["chapters"].append(ch["chapter_name"])
            areas[area]["total_questions"] += ch["total_questions"]
            areas[area]["correct_answers"] += ch["correct_answers"]
            areas[area]["chapter_count"]   += 1

        result = []
        for area_data in areas.values():
            tq = area_data["total_questions"]
            area_data["mastery_percentage"] = (
                round((area_data["correct_answers"] / tq) * 100, 2) if tq > 0 else 0.0
            )
            result.append(area_data)
        return result

    async def calculate_see_readiness(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate SEE readiness as a weighted score across testing areas,
        where each area is weighted by its official NEB marks allocation.
        """
        testing_areas = await self.get_testing_areas_breakdown(user_id)

        total_marks          = sum(a["see_marks"] for a in testing_areas)
        total_weighted_score = sum(
            (a["mastery_percentage"] / 100) * a["see_marks"]
            for a in testing_areas
        )

        readiness_pct = (
            round((total_weighted_score / total_marks) * 100, 2)
            if total_marks > 0 else 0.0
        )

        return {
            "readiness_percentage": readiness_pct,
            "projected_marks":      round(total_weighted_score, 1),
            "total_marks":          total_marks,
            "testing_areas":        testing_areas,
        }

    async def get_recent_activity(
        self, user_id: str, days: int = 30
    ) -> Dict[str, Any]:
        """Return a summary of recent practice activity."""
        now        = datetime.utcnow()
        today      = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago   = now - timedelta(days=7)
        month_ago  = now - timedelta(days=days)

        async def _count(where_clause):
            r = await self.db.execute(select(func.count(StudentInteraction.id)).where(where_clause))
            return r.scalar() or 0

        today_count = await _count(
            and_(StudentInteraction.user_id == user_id,
                 StudentInteraction.created_at >= today)
        )
        month_count = await _count(
            and_(StudentInteraction.user_id == user_id,
                 StudentInteraction.created_at >= month_ago)
        )

        result = await self.db.execute(
            select(
                func.count(StudentInteraction.id),
                func.sum(func.cast(StudentInteraction.is_correct.is_(True), Integer)),
            ).where(
                StudentInteraction.user_id == user_id,
                StudentInteraction.interaction_type == "practice_attempt",
                StudentInteraction.created_at >= week_ago,
            )
        )
        week_count, week_correct = result.first()
        week_count   = week_count   or 0
        week_correct = week_correct or 0

        return {
            "today":         today_count,
            "this_week":     week_count,
            "this_month":    month_count,
            "week_accuracy": round((week_correct / week_count * 100), 2) if week_count else 0.0,
        }

    async def get_daily_activity(
        self, user_id: str, days: int = 7
    ) -> List[Dict[str, Any]]:
        """Return per-day question counts and accuracy for the last N days."""
        now   = datetime.utcnow()
        daily = []

        for i in range(days):
            day_start = (now - timedelta(days=i)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            day_end = day_start + timedelta(days=1)

            result = await self.db.execute(
                select(
                    func.count(StudentInteraction.id),
                    func.sum(func.cast(StudentInteraction.is_correct.is_(True), Integer)),
                ).where(
                    StudentInteraction.user_id == user_id,
                    StudentInteraction.created_at >= day_start,
                    StudentInteraction.created_at < day_end,
                )
            )
            count, correct = result.first()
            count   = count   or 0
            correct = correct or 0

            daily.append({
                "date":      day_start.strftime("%Y-%m-%d"),
                "day_name":  day_start.strftime("%a"),
                "questions": count,
                "accuracy":  round((correct / count * 100), 2) if count else 0.0,
            })

        return daily