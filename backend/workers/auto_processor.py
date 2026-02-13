"""
Automatic content processor - runs continuously in background
Run this: python -m workers.auto_processor

This will automatically process any pending uploads without manual intervention.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import time
from datetime import datetime
import numpy as np
from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models.content import Content
from app.models.processing_queue import ProcessingQueue
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
import fitz


def safe_chunk_text(text, chunk_size=800, overlap=100):
    """Safely chunk text"""
    if not text or len(text) == 0:
        return []
    
    chunks = []
    start = 0
    max_chunks = 10000
    
    while start < len(text) and len(chunks) < max_chunks:
        end = start + chunk_size
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk.strip())
        start += (chunk_size - overlap)
    
    return chunks


async def process_one_task(task, db):
    """Process a single task"""
    
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    print(f"\n{'='*60}")
    print(f"🔄 Processing: {task.id}")
    
    try:
        # Get content
        content_result = await db.execute(
            select(Content).where(Content.id == task.content_id)
        )
        content = content_result.scalar_one_or_none()
        
        if not content:
            task.status = "failed"
            task.error_message = "Content not found"
            await db.commit()
            return False
        
        print(f"📄 {content.title}")
        print(f"   Type: {content.content_type}")
        
        # Update to processing
        task.status = "processing"
        task.started_at = datetime.utcnow()
        content.processing_status = "processing"
        await db.commit()
        
        # Extract text
        print(f"📖 Extracting text...")
        doc = fitz.open(content.file_path)
        total_pages = len(doc)
        
        all_text = ""
        for page_num in range(total_pages):
            all_text += doc[page_num].get_text() + "\n"
        doc.close()
        
        print(f"   Pages: {total_pages}, Characters: {len(all_text):,}")
        
        # Create chunks
        print(f"✂️  Creating chunks...")
        chunks = safe_chunk_text(all_text, chunk_size=800, overlap=100)
        print(f"   Chunks: {len(chunks)}")
        
        if len(chunks) == 0:
            raise Exception("No chunks created")
        
        # Generate embeddings
        print(f"🧮 Generating embeddings...")
        batch_size = 50
        total_added = 0
        
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = []
            batch_metadata = []
            
            for j, chunk in enumerate(batch_chunks):
                embedding = embedding_service.generate_embedding(chunk)
                batch_embeddings.append(embedding)
                
                batch_metadata.append({
                    "content_id": str(content.id),
                    "title": content.title,
                    "content_type": content.content_type,
                    "chunk_index": i + j,
                    "text": chunk[:200]
                })
            
            batch_embeddings_array = np.array(batch_embeddings, dtype='float32')
            vector_store.add_vectors(batch_embeddings_array, batch_metadata)
            total_added += len(batch_embeddings)
            
            # Update progress
            task.progress = (total_added / len(chunks)) * 100
            await db.commit()
        
        print(f"   Embeddings: {total_added}")
        
        # Update to completed
        content.processing_status = "completed"
        content.chunks_count = len(chunks)
        content.embeddings_created = True
        content.page_count = total_pages
        
        task.status = "completed"
        task.progress = 100.0
        task.completed_at = datetime.utcnow()
        task.result = {
            "chunks_created": len(chunks),
            "embeddings_created": len(chunks),
            "pages_processed": total_pages
        }
        
        await db.commit()
        
        print(f"✅ COMPLETED!")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        
        task.status = "failed"
        task.error_message = str(e)
        task.attempts += 1
        task.completed_at = datetime.utcnow()
        content.processing_status = "failed"
        
        await db.commit()
        return False


async def process_pending_queue():
    """Process all pending items in queue"""
    
    async with AsyncSessionLocal() as db:
        # Get pending tasks
        result = await db.execute(
            select(ProcessingQueue)
            .where(ProcessingQueue.status == "pending")
            .order_by(ProcessingQueue.priority.desc())
        )
        pending_tasks = result.scalars().all()
        
        if not pending_tasks:
            return 0
        
        print(f"\n📋 Found {len(pending_tasks)} pending task(s)")
        
        processed = 0
        for task in pending_tasks:
            success = await process_one_task(task, db)
            if success:
                processed += 1
        
        return processed


async def worker_loop():
    """Main worker loop - runs continuously"""
    
    print("="*60)
    print("🤖 AUTOMATIC CONTENT PROCESSOR STARTED")
    print("="*60)
    print("📌 Checking queue every 30 seconds")
    print("📌 Press Ctrl+C to stop")
    print("="*60)
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"\n[{timestamp}] Cycle {iteration}: Checking queue...")
            
            try:
                processed = await process_pending_queue()
                
                if processed > 0:
                    print(f"✅ Processed {processed} item(s)")
                    
                    # Get updated stats
                    vector_store = get_vector_store()
                    stats = vector_store.get_stats()
                    print(f"📊 Total vectors: {stats['total_vectors']:,}")
                else:
                    print(f"💤 No pending tasks")
                    
            except Exception as e:
                print(f"❌ Worker error: {e}")
                import traceback
                traceback.print_exc()
            
            # Wait 30 seconds
            print(f"⏳ Waiting 30 seconds...")
            await asyncio.sleep(30)
            
    except KeyboardInterrupt:
        print("\n\n🛑 WORKER STOPPED BY USER")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(worker_loop())