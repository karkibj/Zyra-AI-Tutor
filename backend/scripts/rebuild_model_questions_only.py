"""
Rebuild ONLY model questions in vector store
Leaves CDC untouched
Run: python scripts/rebuild_model_questions_only.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import numpy as np
from sqlalchemy import select
from app.db import AsyncSessionLocal
from app.models.content import Content
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


async def rebuild_model_questions():
    print("🔄 Rebuilding model questions in vector store...")
    print("   (CDC curriculum will remain untouched)\n")
    
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    
    async with AsyncSessionLocal() as db:
        # Get ONLY model questions
        result = await db.execute(
            select(Content).where(
                Content.content_type == "model_question",
                Content.processing_status == "completed"
            ).order_by(Content.created_at)
        )
        model_questions = result.scalars().all()
        
        if not model_questions:
            print("❌ No completed model questions found!")
            return
        
        print(f"📚 Found {len(model_questions)} model question set(s)\n")
        
        total_added = 0
        
        for content in model_questions:
            print(f"{'='*60}")
            print(f"📄 {content.title}")
            print(f"   Type: {content.content_type}")
            print(f"   File: {content.file_path}")
            
            try:
                # Extract text
                print(f"\n   📖 Step 1: Extracting text from PDF...")
                doc = fitz.open(content.file_path)
                total_pages = len(doc)
                
                all_text = ""
                for page_num in range(total_pages):
                    all_text += doc[page_num].get_text() + "\n"
                doc.close()
                
                print(f"      ✅ Pages: {total_pages}")
                print(f"      ✅ Characters: {len(all_text):,}")
                
                # Create chunks
                print(f"\n   ✂️  Step 2: Creating chunks...")
                chunks = safe_chunk_text(all_text, chunk_size=800, overlap=100)
                print(f"      ✅ Chunks created: {len(chunks)}")
                
                if len(chunks) == 0:
                    print(f"      ⚠️  No chunks created, skipping")
                    continue
                
                # Generate embeddings
                print(f"\n   🧮 Step 3: Generating embeddings...")
                
                batch_embeddings = []
                batch_metadata = []
                
                for j, chunk in enumerate(chunks):
                    embedding = embedding_service.generate_embedding(chunk)
                    batch_embeddings.append(embedding)
                    
                    # ✅ CREATE PROPER METADATA
                    batch_metadata.append({
                        "content_id": str(content.id),
                        "title": content.title,
                        "content_type": content.content_type,
                        "chunk_index": j,
                        "text": chunk[:200]  # First 200 chars as preview
                    })
                
                print(f"      ✅ Embeddings generated: {len(batch_embeddings)}")
                
                # Convert to numpy array
                print(f"\n   💾 Step 4: Adding to vector store...")
                batch_embeddings_array = np.array(batch_embeddings, dtype='float32')
                
                # Add to vector store
                vector_store.add_vectors(batch_embeddings_array, batch_metadata)
                total_added += len(chunks)
                
                print(f"      ✅ Added {len(chunks)} vectors to FAISS")
                print(f"\n   ✅ {content.title} - COMPLETE!\n")
                
            except Exception as e:
                print(f"\n   ❌ ERROR: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"{'='*60}")
        print(f"✅ MODEL QUESTIONS PROCESSING COMPLETE!")
        print(f"{'='*60}")
        print(f"   Vectors added: {total_added}")
        
        # Verify
        stats = vector_store.get_stats()
        print(f"\n📊 Vector Store Stats:")
        print(f"   Total vectors now: {stats['total_vectors']:,}")
        print(f"   (CDC: ~2,196 + Model Questions: {total_added})")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎯 MODEL QUESTIONS VECTOR STORE REBUILDER")
    print("="*60)
    print("This will add model questions to FAISS with proper metadata.")
    print("CDC curriculum vectors will NOT be touched.")
    print("="*60 + "\n")
    
    input("Press ENTER to start...")
    
    asyncio.run(rebuild_model_questions())
    
    print("✅ Done! You can now test the AI tutor.\n")