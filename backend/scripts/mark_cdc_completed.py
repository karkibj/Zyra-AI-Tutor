"""
Mark CDC curriculum as completed (since it's already processed)
Run: python scripts/mark_cdc_completed.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.content import Content
from app.models.processing_queue import ProcessingQueue
from app.services.vector_store_service import get_vector_store

async def mark_cdc_completed():
    """Mark CDC content as completed"""
    
    async with AsyncSessionLocal() as db:
        # Find CDC content
        result = await db.execute(
            select(Content).where(
                Content.title.like('%CDC%'),
                Content.content_type == 'curriculum'
            )
        )
        cdc_contents = result.scalars().all()
        
        if not cdc_contents:
            print("❌ No CDC content found")
            return
        
        print(f"📋 Found {len(cdc_contents)} CDC content items:")
        
        for content in cdc_contents:
            print(f"\n{'='*60}")
            print(f"📄 {content.title}")
            print(f"   Current status: {content.processing_status}")
            print(f"   Chunks: {content.chunks_count}")
            print(f"   Embeddings: {content.embeddings_created}")
            
            # Update content status
            content.processing_status = "completed"
            
            # If chunks not set, set based on vector store
            if not content.chunks_count:
                vector_store = get_vector_store()
                stats = vector_store.get_stats()
                # Assume CDC has most of the vectors (it was processed first)
                content.chunks_count = stats.get('total_vectors', 2196)
            
            content.embeddings_created = True
            
            # Update any pending queue items
            queue_result = await db.execute(
                select(ProcessingQueue).where(
                    ProcessingQueue.content_id == content.id,
                    ProcessingQueue.status == "pending"
                )
            )
            queue_items = queue_result.scalars().all()
            
            for queue_item in queue_items:
                print(f"   ✅ Marking queue item as completed")
                queue_item.status = "completed"
                queue_item.progress = 100.0
                queue_item.result = {
                    "note": "Already processed - marked completed manually"
                }
            
            print(f"   ✅ Updated to: {content.processing_status}")
        
        await db.commit()
        print(f"\n{'='*60}")
        print(f"✅ All CDC content marked as completed!")

if __name__ == "__main__":
    print("🚀 Marking CDC content as completed...")
    asyncio.run(mark_cdc_completed())