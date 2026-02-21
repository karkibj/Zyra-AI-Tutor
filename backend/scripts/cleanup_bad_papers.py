"""
Delete past papers with no metadata
Run: python scripts/cleanup_bad_papers.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from sqlalchemy import select, delete
from app.db import AsyncSessionLocal
from app.models.content import Content
from pathlib import Path

async def cleanup_bad_papers():
    async with AsyncSessionLocal() as db:
        # Find bad papers
        result = await db.execute(
            select(Content).where(Content.content_type == "past_paper")
        )
        papers = result.scalars().all()
        
        deleted = 0
        for paper in papers:
            # Check if metadata is bad
            metadata = paper.content_metadata
            if not metadata or not isinstance(metadata, dict):
                print(f"❌ Deleting: {paper.title} (no metadata)")
                
                # Delete file
                try:
                    file_path = Path(paper.file_path)
                    if file_path.exists():
                        file_path.unlink()
                        print(f"   🗑️  File deleted")
                except:
                    pass
                
                # Delete from DB
                await db.delete(paper)
                deleted += 1
                continue
            
            # Check if exam info exists
            exam_info = metadata.get("exam", {})
            if not exam_info.get("year") or not exam_info.get("province"):
                print(f"❌ Deleting: {paper.title} (incomplete metadata)")
                
                # Delete file
                try:
                    file_path = Path(paper.file_path)
                    if file_path.exists():
                        file_path.unlink()
                except:
                    pass
                
                await db.delete(paper)
                deleted += 1
        
        await db.commit()
        print(f"\n✅ Deleted {deleted} bad papers")

if __name__ == "__main__":
    print("🧹 Cleaning up bad past papers...")
    asyncio.run(cleanup_bad_papers())