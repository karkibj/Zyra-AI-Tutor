"""
Reset Failed Content
Resets failed content and creates new processing tasks
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.content import Content
from app.models.processing_queue import ProcessingQueue
from sqlalchemy import select


async def reset_failed_content():
    """Reset all failed content and recreate processing tasks"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all failed content
            result = await db.execute(
                select(Content).where(Content.processing_status == 'failed')
            )
            failed_content = result.scalars().all()
            
            if not failed_content:
                print("✅ No failed content found!")
                return
            
            print(f"\n📋 Found {len(failed_content)} failed content item(s)")
            print("="*60)
            
            for content in failed_content:
                print(f"\n📄 Content: {content.title}")
                print(f"   ID: {content.id}")
                print(f"   Type: {content.content_type}")
                print(f"   Status: {content.processing_status}")
                
                # Reset content status
                content.processing_status = 'pending'
                content.chunks_count = 0
                content.embeddings_created = False
                content.vector_store_id = None
                
                # Clear processing metadata
                if content.metadata and 'processed_at' in content.metadata:
                    del content.metadata['processed_at']
                
                print(f"   ✅ Reset content to pending")
                
                # Check if queue task already exists
                queue_result = await db.execute(
                    select(ProcessingQueue).where(
                        ProcessingQueue.content_id == content.id,
                        ProcessingQueue.task_type == 'extract_text'
                    )
                )
                existing_task = queue_result.scalar_one_or_none()
                
                if existing_task:
                    # Reset existing task
                    existing_task.status = 'pending'
                    existing_task.attempts = 0
                    existing_task.progress = 0.0
                    existing_task.error_message = None
                    existing_task.result = None
                    existing_task.started_at = None
                    existing_task.completed_at = None
                    print(f"   ♻️  Reset existing queue task")
                else:
                    # Create new queue task
                    new_task = ProcessingQueue(
                        content_id=content.id,
                        task_type='extract_text',
                        status='pending',
                        priority=10
                    )
                    db.add(new_task)
                    print(f"   ➕ Created new queue task")
            
            await db.commit()
            
            print("\n" + "="*60)
            print(f"🎉 SUCCESS! Reset {len(failed_content)} content item(s)")
            print("="*60)
            print("\n💡 Now run the worker: python run_worker.py\n")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(reset_failed_content())