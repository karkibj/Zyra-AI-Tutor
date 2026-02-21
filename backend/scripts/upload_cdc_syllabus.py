"""
Upload CDC Syllabus to Zyra Knowledge Base
"""
import asyncio
import sys
import uuid
import shutil
from pathlib import Path

from sqlalchemy import select

# Ensure app is importable
sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.content import Content
from app.models.curriculum import CurriculumNode, ContentCurriculumMapping
from app.models.processing_queue import ProcessingQueue


async def upload_cdc_syllabus():
    """Upload CDC syllabus PDF"""

    async with AsyncSessionLocal() as db:
        try:
            print("🚀 Uploading CDC Grade 10 Mathematics Syllabus...")

            # Path to CDC PDF
            cdc_pdf_path = Path("data/raw/cdc.pdf")

            if not cdc_pdf_path.exists():
                print("❌ CDC PDF not found!")
                return

            # File metadata
            file_size = cdc_pdf_path.stat().st_size

            # ✅ UUID OBJECT (NOT STRING)
            content_id = uuid.uuid4()

            # Upload destination
            uploads_dir = Path("uploads/content")
            uploads_dir.mkdir(parents=True, exist_ok=True)

            dest_path = uploads_dir / f"{content_id}.pdf"
            shutil.copy(cdc_pdf_path, dest_path)

            print(f"✅ File copied to: {dest_path}")

            # Create content record
            content = Content(
                id=content_id,
                title="CDC Grade 10 Mathematics Syllabus 2023",
                description="Official Curriculum Development Centre textbook for Grade 10 Mathematics",
                content_type="curriculum",
                file_path=str(dest_path),
                file_type="pdf",
                file_size=file_size,
                page_count=310,
                processing_status="pending",
                metadata={
                    "source": "CDC Official",
                    "year": 2023,
                    "board": "CDC",
                    "grade": 10,
                    "subject": "Mathematics",
                    "chapters": 14,
                    "total_pages": 310
                }
            )

            db.add(content)
            await db.flush()  # ensures content exists for FK usage

            print("✅ Content record created")

            # Fetch all Grade 10 Math chapters
            result = await db.execute(
                select(CurriculumNode).where(
                    CurriculumNode.code.like("CDC-10-MATH-CH%"),
                    CurriculumNode.active.is_(True)
                )
            )
            chapters = result.scalars().all()

            # Map content to chapters
            for chapter in chapters:
                db.add(
                    ContentCurriculumMapping(
                        content_id=content_id,
                        curriculum_node_id=chapter.id,
                        relevance_score=1.0,
                        tags=["official", "syllabus", "cdc", "textbook"],
                        mapping_type="primary"
                    )
                )

            print(f"✅ Mapped to {len(chapters)} chapters")

            # Add processing queue entry
            db.add(
                ProcessingQueue(
                    content_id=content_id,
                    task_type="extract_text",
                    status="pending",
                    priority=10
                )
            )

            await db.commit()

            print("\n🎉 SUCCESS!")
            print(f"   Content ID: {content_id}")
            print(f"   File: {dest_path}")
            print(f"   Size: {file_size / 1024 / 1024:.2f} MB")
            print(f"   Chapters mapped: {len(chapters)}")

        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(upload_cdc_syllabus())
