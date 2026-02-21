"""
Reset Failed Tasks
Resets failed processing tasks back to pending
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.processing_queue import ProcessingQueue
from sqlalchemy import select, update


async def reset_failed_tasks():
    """Reset all failed tasks to pending"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Get all failed tasks
            result = await db.execute(
                select(ProcessingQueue).where(ProcessingQueue.status == 'failed')
            )
            failed_tasks = result.scalars().all()
            
            if not failed_tasks:
                print("✅ No failed tasks found!")
                return
            
            print(f"\n📋 Found {len(failed_tasks)} failed task(s)")
            print("="*60)
            
            for task in failed_tasks:
                print(f"\nTask ID: {task.id}")
                print(f"Content ID: {task.content_id}")
                print(f"Task Type: {task.task_type}")
                print(f"Attempts: {task.attempts}/{task.max_attempts}")
                print(f"Error: {task.error_message}")
                
                # Reset to pending
                task.status = 'pending'
                task.attempts = 0  # Reset attempts
                task.error_message = None
                task.started_at = None
                task.completed_at = None
                
                print("✅ Reset to pending")
            
            await db.commit()
            
            print("\n" + "="*60)
            print(f"🎉 SUCCESS! Reset {len(failed_tasks)} task(s) to pending")
            print("="*60)
            print("\n💡 Now run the worker: python run_worker.py\n")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(reset_failed_tasks())