"""
Process uploaded content from processing queue
Run this: python scripts/process_uploaded_content.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import numpy as np  # ✅ ADDED
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.content import Content
from app.models.processing_queue import ProcessingQueue
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
import fitz  # PyMuPDF


def safe_chunk_text(text, chunk_size=800, overlap=100):
    """Safely chunk text with safety limit"""
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


async def process_pending_content():
    """Process all pending content in the queue"""
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ProcessingQueue)
            .where(ProcessingQueue.status == "pending")
            .order_by(ProcessingQueue.priority.desc())
        )
        pending_tasks = result.scalars().all()
        
        if not pending_tasks:
            print("📭 No pending tasks in queue")
            return
        
        print(f"📋 Found {len(pending_tasks)} pending task(s)\n")
        
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        
        for task in pending_tasks:
            print(f"{'='*60}")
            print(f"🔄 Processing task: {task.id}")
            print(f"   Content ID: {task.content_id}")
            
            try:
                content_result = await db.execute(
                    select(Content).where(Content.id == task.content_id)
                )
                content = content_result.scalar_one_or_none()
                
                if not content:
                    print(f"❌ Content not found")
                    task.status = "failed"
                    task.error_message = "Content not found"
                    await db.commit()
                    continue
                
                print(f"📄 Processing: {content.title}")
                print(f"   Type: {content.content_type}")
                print(f"   File: {content.file_path}")
                
                task.status = "processing"
                content.processing_status = "processing"
                await db.commit()
                
                # Extract text
                print(f"\n📖 Step 1: Extracting text from PDF...")
                doc = fitz.open(content.file_path)
                total_pages = len(doc)
                print(f"   Pages: {total_pages}")
                
                all_text = ""
                for page_num in range(total_pages):
                    page = doc[page_num]
                    all_text += page.get_text() + "\n"
                
                doc.close()
                print(f"   ✅ Extracted {len(all_text):,} characters")
                
                # Create chunks
                print(f"\n✂️  Step 2: Creating text chunks...")
                chunks = safe_chunk_text(all_text, chunk_size=800, overlap=100)
                print(f"   ✅ Created {len(chunks)} chunks")
                
                if len(chunks) == 0:
                    raise Exception("No chunks created")
                
                # Generate embeddings
                print(f"\n🧮 Step 3: Generating embeddings and storing in FAISS...")
                
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
                    
                    # ✅ CONVERT TO NUMPY ARRAY
                    batch_embeddings_array = np.array(batch_embeddings, dtype='float32')
                    
                    vector_store.add_vectors(batch_embeddings_array, batch_metadata)
                    total_added += len(batch_embeddings)
                    
                    print(f"   Progress: {total_added}/{len(chunks)} embeddings added")
                
                print(f"   ✅ All {total_added} embeddings stored successfully")
                
                # Update database
                print(f"\n💾 Step 4: Updating database records...")
                content.processing_status = "completed"
                content.chunks_count = len(chunks)
                content.embeddings_created = True
                content.page_count = total_pages
                
                task.status = "completed"
                task.progress = 100.0
                task.result = {
                    "chunks_created": len(chunks),
                    "embeddings_created": len(chunks),
                    "pages_processed": total_pages,
                    "characters_extracted": len(all_text)
                }
                
                await db.commit()
                print(f"   ✅ Database updated")
                
                print(f"\n✅ PROCESSING COMPLETED SUCCESSFULLY!")
                print(f"   📄 Content: {content.title}")
                print(f"   📑 Pages: {total_pages}")
                print(f"   ✂️  Chunks: {len(chunks)}")
                print(f"   🧮 Embeddings: {len(chunks)}")
                print(f"   📊 Status: {content.processing_status}\n")
                
            except Exception as e:
                print(f"\n❌ ERROR PROCESSING CONTENT!")
                print(f"   Error: {str(e)}")
                import traceback
                traceback.print_exc()
                
                task.status = "failed"
                task.error_message = str(e)
                task.attempts += 1
                content.processing_status = "failed"
                
                await db.commit()
                print(f"   Status marked as: FAILED\n")
        
        print(f"{'='*60}")
        print(f"📊 PROCESSING SESSION COMPLETE!")
        stats = vector_store.get_stats()
        print(f"   Total vectors in FAISS: {stats['total_vectors']:,}")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    print("🚀 Starting content processing...\n")
    asyncio.run(process_pending_content())