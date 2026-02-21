"""
Rebuild CDC curriculum in vector store - SAFE BATCHED VERSION
Uses memory-efficient batching to prevent freezing
Run: python scripts/rebuild_cdc_safe.py
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
    """Safely chunk text with memory management"""
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


async def rebuild_cdc():
    print("\n" + "="*70)
    print("🎓 CDC CURRICULUM VECTOR STORE REBUILDER")
    print("="*70)
    print("This will process CDC curriculum with proper metadata.")
    print("Using BATCHED processing to prevent device lag.")
    print("="*70 + "\n")
    
    # Get services
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    async with AsyncSessionLocal() as db:
        # Find CDC content
        print("🔍 Looking for CDC curriculum...")
        
        result = await db.execute(
            select(Content).where(
                Content.content_type == "curriculum",
                Content.title.contains("CDC")
            )
        )
        content = result.scalar_one_or_none()
        
        if not content:
            print("❌ CDC curriculum not found in database!")
            return
        
        print(f"✅ Found: {content.title}")
        print(f"   ID: {content.id}")
        print(f"   File: {content.file_path}")
        print(f"   Current status: {content.processing_status}")
        
        # Check file exists
        file_path = Path(content.file_path)
        if not file_path.exists():
            # Try project location
            file_path = Path("/mnt/project/cdc.pdf")
            if not file_path.exists():
                print(f"❌ File not found!")
                return
        
        print(f"   File size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        print("\n" + "="*70)
        print("⚠️  PROCESSING PLAN:")
        print("="*70)
        print("📄 Extract text from ~310 pages (2-3 minutes)")
        print("✂️  Create chunks in batches (prevents memory issues)")
        print("🧮 Generate embeddings in small batches (20 at a time)")
        print("💾 Save to FAISS with proper metadata")
        print("⏱️  Total time: ~15-20 minutes")
        print("="*70)
        
        confirm = input("\n⏸️  Continue? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Cancelled by user")
            return
        
        # =================================================================
        # STEP 1: EXTRACT TEXT
        # =================================================================
        print("\n" + "="*70)
        print("📄 STEP 1: EXTRACTING TEXT FROM PDF")
        print("="*70)
        print("📖 Processing all pages... (this takes 2-3 minutes)")
        print("   ⏳ Please wait, device may lag slightly...")
        print()
        
        try:
            doc = fitz.open(str(file_path))
            total_pages = len(doc)
            
            all_text = ""
            for page_num in range(total_pages):
                all_text += doc[page_num].get_text() + "\n"
                
                # Progress indicator
                if (page_num + 1) % 50 == 0:
                    print(f"   Processed {page_num + 1}/{total_pages} pages...")
            
            doc.close()
            
            print(f"\n✅ EXTRACTION COMPLETE!")
            print(f"   Pages: {total_pages}")
            print(f"   Characters: {len(all_text):,}")
            
        except Exception as e:
            print(f"\n❌ Extraction failed: {e}")
            return
        
        input("\n⏸️  Press ENTER to continue to chunking...")
        
        # =================================================================
        # STEP 2: CREATE CHUNKS (BATCHED)
        # =================================================================
        print("\n" + "="*70)
        print("✂️  STEP 2: CREATING TEXT CHUNKS")
        print("="*70)
        print("🔄 Processing in 50,000 character batches...")
        print("   (Prevents memory overflow)")
        print()
        
        all_chunks = []
        batch_size = 50000
        
        for i in range(0, len(all_text), batch_size):
            batch_text = all_text[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(all_text) + batch_size - 1) // batch_size
            
            print(f"   Batch {batch_num}/{total_batches}...", end=" ", flush=True)
            
            batch_chunks = safe_chunk_text(
                batch_text,
                chunk_size=800,
                overlap=100
            )
            
            all_chunks.extend(batch_chunks)
            print(f"✓ {len(batch_chunks)} chunks")
            
            gc.collect()
            await asyncio.sleep(0.2)
        
        print(f"\n✅ CHUNKING COMPLETE!")
        print(f"   Total chunks: {len(all_chunks)}")
        
        input("\n⏸️  Press ENTER to continue to embeddings...")
        
        # =================================================================
        # STEP 3: GENERATE EMBEDDINGS (BATCHED)
        # =================================================================
        print("\n" + "="*70)
        print("🧮 STEP 3: GENERATING EMBEDDINGS")
        print("="*70)
        print(f"📊 Processing {len(all_chunks)} chunks")
        print("🔄 Batches of 20 chunks at a time...")
        print()
        
        embed_batch_size = 20
        total_batches = (len(all_chunks) + embed_batch_size - 1) // embed_batch_size
        total_added = 0
        
        for i in range(0, len(all_chunks), embed_batch_size):
            batch_chunks = all_chunks[i:i + embed_batch_size]
            batch_num = (i // embed_batch_size) + 1
            
            print(f"   Batch {batch_num}/{total_batches} ({len(batch_chunks)} chunks)...", end=" ", flush=True)
            
            # Generate embeddings for this batch
            batch_embeddings = []
            batch_metadata = []
            
            for j, chunk in enumerate(batch_chunks):
                embedding = embedding_service.generate_embedding(chunk)
                batch_embeddings.append(embedding)
                
                # ✅ CREATE PROPER METADATA
                batch_metadata.append({
                    "content_id": str(content.id),
                    "title": content.title,
                    "content_type": content.content_type,
                    "chunk_index": i + j,
                    "text": chunk[:200]  # First 200 chars as preview
                })
            
            # Convert to numpy array
            batch_embeddings_array = np.array(batch_embeddings, dtype='float32')
            
            # Add to vector store
            vector_store.add_vectors(batch_embeddings_array, batch_metadata)
            total_added += len(batch_embeddings)
            
            print("✓")
            gc.collect()
            await asyncio.sleep(0.5)
        
        print(f"\n✅ EMBEDDINGS COMPLETE!")
        print(f"   Total embeddings: {total_added}")
        
        # =================================================================
        # STEP 4: UPDATE DATABASE
        # =================================================================
        print("\n" + "="*70)
        print("💾 STEP 4: UPDATING DATABASE")
        print("="*70)
        
        content.processing_status = "completed"
        content.chunks_count = len(all_chunks)
        content.embeddings_created = True
        content.page_count = total_pages
        
        await db.commit()
        
        print("✅ Database updated")
        
        # =================================================================
        # FINAL STATS
        # =================================================================
        stats = vector_store.get_stats()
        
        print("\n" + "="*70)
        print("🎉 CDC PROCESSING COMPLETE!")
        print("="*70)
        print(f"📄 Pages processed: {total_pages}")
        print(f"✂️  Chunks created: {len(all_chunks)}")
        print(f"🧮 Embeddings generated: {total_added}")
        print(f"📊 Total vectors in store: {stats['total_vectors']:,}")
        print(f"💾 Status: {content.processing_status}")
        print("="*70)
        print()
        print("✅ CDC curriculum is now ready with proper metadata!")
        print("💬 AI can now cite 'CDC Grade 10 Mathematics Syllabus 2023'")
        print("="*70 + "\n")


if __name__ == "__main__":
    print("\n🚀 CDC Curriculum Rebuilder")
    print("⏱️  Estimated time: 15-20 minutes")
    print("💻 Keep device plugged in\n")
    
    try:
        asyncio.run(rebuild_cdc())
        print("✅ Processing completed successfully!\n")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()