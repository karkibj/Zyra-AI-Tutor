"""
verify_progress.py
Verify progress tracking is working end-to-end.
Run from backend/ then delete.

    python verify_progress.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from dotenv import load_dotenv
load_dotenv()

async def verify():
    from app.db import AsyncSessionLocal
    from app.models.progress import StudentInteraction, TopicMastery
    from app.models.user import User
    from sqlalchemy import select, func
    from collections import Counter

    async with AsyncSessionLocal() as db:
        print("=" * 60)
        print("PROGRESS TRACKING VERIFICATION")
        print("=" * 60)

        # 1. Check student_interactions
        result = await db.execute(select(func.count(StudentInteraction.id)))
        total_interactions = result.scalar()

        result = await db.execute(
            select(StudentInteraction.interaction_type, func.count())
            .group_by(StudentInteraction.interaction_type)
        )
        by_type = dict(result.all())

        print(f"\n[1] student_interactions table:")
        print(f"    Total: {total_interactions}")
        for t, c in by_type.items():
            print(f"    {t}: {c}")

        # 2. Check topic_mastery
        result = await db.execute(select(TopicMastery))
        masteries = result.scalars().all()

        print(f"\n[2] topic_mastery table:")
        print(f"    Total records: {len(masteries)}")

        chat_engaged = [m for m in masteries if m.total_questions_attempted == 0]
        practiced = [m for m in masteries if m.total_questions_attempted > 0]
        print(f"    Chat-explored (0 questions): {len(chat_engaged)}")
        print(f"    Practiced: {len(practiced)}")

        if masteries:
            print(f"\n    Topics:")
            for m in sorted(masteries, key=lambda x: x.mastery_percentage, reverse=True):
                print(f"      {m.topic}: {m.mastery_percentage:.0f}% ({m.total_questions_attempted} questions)")

        # 3. Check SEE readiness calculation
        print(f"\n[3] SEE Readiness check:")
        from app.services.progress_service import ProgressTrackingService

        # Get first user
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()

        if user:
            service = ProgressTrackingService(db)
            chapters = await service._get_chapters_from_db()
            total_marks = sum(c['see_marks'] for c in chapters)
            print(f"    Total SEE marks from chapters: {total_marks}")
            print(f"    Chapters with marks > 0: {sum(1 for c in chapters if c['see_marks'] > 0)}/15")

            readiness = await service.calculate_see_readiness(user.id)
            print(f"    SEE Readiness for {user.email}: {readiness['readiness_percentage']:.1f}%")
            print(f"    Projected marks: {readiness['projected_marks']:.1f}/75")

            # Check recommendations
            recs = await service.get_weak_areas(user.id, threshold=75.0)
            print(f"\n[4] Weak areas (below 75%): {len(recs)}")
            for r in recs[:3]:
                print(f"    {r.topic}: {r.mastery_percentage:.0f}%")
        else:
            print("    No users found")

        print("\n[OK] Verification complete. Delete this script.")

asyncio.run(verify())