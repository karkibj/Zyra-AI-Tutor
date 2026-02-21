"""
Process CDC - COMPLETE WORKING VERSION
"""
import asyncio
import sys
from pathlib import Path
import gc

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.content import Content
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
from sqlalchemy import select
import fitz
import numpy as np


def safe_chunk_text(text: str, chunk_size: int = 800, overlap: int = 100):
    """Safe chunking that won't hang"""
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk_text = text[start:end].strip()
        
        if chunk_text:
            chunks.append({
                'text': chunk_text,
                'chunk_index': len(chunks)
            })
        
        if end >= text_len:
            break
        
        start = end - overlap
        
        if len(chunks) > 10000:
            print(f"   ⚠️ Safety limit reached ({len(chunks)} chunks)")
            break
    
    return chunks


async def process_cdc():
    """Process CDC curriculum"""
    
    print("\n" + "="*70)
    print("🎓 PROCESSING CDC CURRICULUM")
    print("="*70 + "\n")
    
    async with AsyncSessionLocal() as db:
        # Find CDC content
        result = await db.execute(
            select(Content).where(
                Content.title.contains("CDC"),
                Content.content_type == "curriculum"
            )
        )
        content = result.scalars().first()
        
        if not content:
            print("❌ CDC content not found in database!")
            return
        
        print(f"✅ Found: {content.title}")
        print(f"   ID: {content.id}")
        
        # Locate file
        file_path = Path(content.file_path)
        if not file_path.exists():
            file_path = Path("/mnt/project/cdc.pdf")
        
        if not file_path.exists():
            print("❌ File not found!")
            return
        
        print(f"   File: {file_path}")
        print(f"   Size: {file_path.stat().st_size / 1024 / 1024:.2f} MB\n")
        
        input("⏸️  Press ENTER to start...")
        
        # STEP 1: Extract text
        print("\n📄 STEP 1: EXTRACTING TEXT")
        print("="*70)
        print("📖 Reading PDF (2-3 minutes)...\n")
        
        doc = fitz.open(str(file_path))
        total_pages = len(doc)
        full_text = ""
        
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            full_text += text + "\n\n"
            
            if (page_num + 1) % 50 == 0:
                print(f"   ... {page_num + 1}/{total_pages} pages")
        
        doc.close()
        
        print(f"\n✅ STEP 1 COMPLETE")
        print(f"   Pages: {total_pages}")
        print(f"   Characters: {len(full_text):,}")
        
        input("\n⏸️  Press ENTER to continue...")
        
        # STEP 2: Create chunks
        print("\n📦 STEP 2: CHUNKING")
        print("="*70)
        print("🔄 Creating text chunks...\n")
        
        all_chunks = safe_chunk_text(full_text, chunk_size=800, overlap=100)
        
        print(f"✅ STEP 2 COMPLETE: {len(all_chunks)} chunks created")
        
        input("\n⏸️  Press ENTER to continue to embeddings...")
        
        # STEP 3: Generate embeddings and store
        print("\n🧠 STEP 3: EMBEDDINGS & STORAGE")
        print("="*70)
        print(f"📊 Processing {len(all_chunks)} chunks in batches of 50\n")
        
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        
        batch_size = 50
        total_batches = (len(all_chunks) + batch_size - 1) // batch_size
        
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ", flush=True)
            
            # Extract texts
            texts = [c['text'] for c in batch]
            
            # Generate embeddings
            embeddings = embedding_service.generate_embeddings(texts)
            
            # Prepare metadata
            metadata = [
                {
                    'content_id': str(content.id),
                    'text': chunk['text'],
                    'chunk_index': i + j,
                    'source': 'cdc_curriculum',
                    'title': content.title
                }
                for j, chunk in enumerate(batch)
            ]
            
            # Add to vector store
            vector_store.add_vectors(embeddings, metadata)
            
            print("✓")
            gc.collect()
            await asyncio.sleep(0.3)
        
        print(f"\n✅ STEP 3 COMPLETE: {len(all_chunks)} embeddings stored")
        
        # STEP 4: Update database
        print("\n💾 STEP 4: UPDATING DATABASE")
        print("="*70)
        
        content.processing_status = "completed"
        content.chunks_count = len(all_chunks)
        content.embeddings_created = True
        
        # Update metadata safely (it's a JSON column)
        # if content.metadata is None:
        #     content.metadata = {}
        
        # content.metadata["processing_complete"] = True
        # content.metadata["chunk_size"] = 800
        # content.metadata["chunk_overlap"] = 100
        
        await db.commit()
        
        print("✅ Database updated")
        
        
        # Get vector store stats
        stats = vector_store.get_stats()
        
        # Final summary
        print("\n" + "="*70)
        print("🎉 CDC PROCESSING COMPLETE!")
        print("="*70)
        print(f"📄 Pages processed: {total_pages}")
        print(f"📦 Text chunks: {len(all_chunks)}")
        print(f"🧠 Embeddings created: {len(all_chunks)}")
        print(f"💾 Total vectors in store: {stats['total_vectors']}")
        print(f"✅ Status: {content.processing_status}")
        print("="*70)
        print()
        print("✅ CDC is now ready for student questions!")
        print("💬 Students can ask about any topic in the curriculum")
        print("🎓 Try asking: 'What is compound interest?' or 'Solve quadratic equations'")
        print()


if __name__ == "__main__":
    print("\n🚀 CDC Processing Script")
    print("⏱️  Estimated time: 12-15 minutes")
    print("💻 Keep device plugged in\n")
    
    try:
        asyncio.run(process_cdc())
        print("✅ Processing completed successfully!\n")
    except KeyboardInterrupt:
        print("\n⚠️ Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()