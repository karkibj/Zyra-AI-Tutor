"""
CLEAR vector store and rebuild from scratch
Run: python scripts/clear_and_rebuild_all.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import numpy as np
import gc
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.content import Content
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
import fitz
from pathlib import Path

def safe_chunk_text(text, chunk_size=800, overlap=100):
    """Safely chunk text"""
    if not text or len(text) == 0:
        return []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk:
            chunks.append(chunk.strip())
        start += (chunk_size - overlap)
    
    return chunks


async def clear_and_rebuild():
    print("\n" + "="*70)
    print("🔄 CLEAR AND REBUILD VECTOR STORE")
    print("="*70)
    print("⚠️  This will DELETE all existing vectors and rebuild from scratch")
    print("="*70 + "\n")
    
    confirm = input("⏸️  Continue? (type 'YES' to confirm): ")
    if confirm != 'YES':
        print("❌ Cancelled")
        return
    
    # Get services
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    # ✅ CLEAR EVERYTHING
    print("\n🗑️  CLEARING OLD DATA...")
    vector_store.index = None
    vector_store.metadata_list = []
    
    # Delete files
    if vector_store.index_file.exists():
        vector_store.index_file.unlink()
        print("   ✅ Deleted old index file")
    if vector_store.metadata_file.exists():
        vector_store.metadata_file.unlink()
        print("   ✅ Deleted old metadata file")
    
    print("✅ Vector store cleared!\n")
    
    async with AsyncSessionLocal() as db:
        # Get all completed content
        result = await db.execute(
            select(Content).where(
                Content.processing_status == "completed",
                Content.embeddings_created == True
            ).order_by(Content.content_type, Content.created_at)
        )
        contents = result.scalars().all()
        
        print(f"📚 Found {len(contents)} documents to process\n")
        
        for idx, content in enumerate(contents, 1):
            print(f"\n{'='*70}")
            print(f"📄 [{idx}/{len(contents)}] {content.title}")
            print(f"   Type: {content.content_type}")
            print(f"   File: {content.file_path}")
            print(f"{'='*70}")
            
            try:
                # Extract text
                print(f"\n   📖 Extracting text...")
                doc = fitz.open(content.file_path)
                total_pages = len(doc)
                
                all_text = ""
                for page_num in range(total_pages):
                    all_text += doc[page_num].get_text() + "\n"
                doc.close()
                
                print(f"      ✅ Pages: {total_pages}")
                print(f"      ✅ Characters: {len(all_text):,}")
                
                # Create chunks
                print(f"\n   ✂️  Creating chunks...")
                chunks = safe_chunk_text(all_text, chunk_size=800, overlap=100)
                print(f"      ✅ Chunks: {len(chunks)}")
                
                if len(chunks) == 0:
                    print(f"      ⚠️  No chunks, skipping")
                    continue
                
                # Generate embeddings in batches
                print(f"\n   🧮 Generating embeddings...")
                
                batch_size = 20
                total_batches = (len(chunks) + batch_size - 1) // batch_size
                
                for i in range(0, len(chunks), batch_size):
                    batch_chunks = chunks[i:i + batch_size]
                    batch_num = (i // batch_size) + 1
                    
                    print(f"      Batch {batch_num}/{total_batches}...", end=" ", flush=True)
                    
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
                    
                    # Add to vector store
                    batch_embeddings_array = np.array(batch_embeddings, dtype='float32')
                    vector_store.add_vectors(batch_embeddings_array, batch_metadata)
                    
                    print("✓")
                    gc.collect()
                    await asyncio.sleep(0.3)
                
                print(f"\n   ✅ {content.title} complete!")
                
            except Exception as e:
                print(f"\n   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Final stats
        stats = vector_store.get_stats()
        
        print(f"\n{'='*70}")
        print(f"🎉 REBUILD COMPLETE!")
        print(f"{'='*70}")
        print(f"📊 Total vectors: {stats['total_vectors']:,}")
        print(f"📊 Total metadata: {stats['metadata_count']:,}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(clear_and_rebuild())