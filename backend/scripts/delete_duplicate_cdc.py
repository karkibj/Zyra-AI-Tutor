"""
Delete duplicate CDC entries (keep only one)
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.content import Content
from sqlalchemy import select, delete


async def cleanup_duplicates():
    """Remove duplicate CDC entries"""
    
    async with AsyncSessionLocal() as db:
        # Find all CDC entries
        result = await db.execute(
            select(Content).where(
                Content.title.contains("CDC"),
                Content.content_type == "curriculum"
            ).order_by(Content.created_at)
        )
        cdc_entries = result.scalars().all()
        
        print(f"\n🔍 Found {len(cdc_entries)} CDC entries:\n")
        
        for i, entry in enumerate(cdc_entries, 1):
            print(f"{i}. ID: {entry.id}")
            print(f"   Title: {entry.title}")
            print(f"   Status: {entry.processing_status}")
            print(f"   Created: {entry.created_at}")
            print(f"   File: {entry.file_path}")
            print()
        
        if len(cdc_entries) <= 1:
            print("✅ No duplicates found!")
            return
        
        # Keep the first one, delete the rest
        keep = cdc_entries[0]
        duplicates = cdc_entries[1:]
        
        print(f"✅ Keeping: {keep.id} (oldest)")
        print(f"🗑️  Deleting {len(duplicates)} duplicate(s)...\n")
        
        for dup in duplicates:
            print(f"   Deleting: {dup.id}...")
            await db.delete(dup)
        
        await db.commit()
        
        print(f"\n✅ Cleanup complete! Only 1 CDC entry remains.")
        print(f"   ID: {keep.id}")
        print(f"   Status: {keep.processing_status}")


if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())