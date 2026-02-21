"""
Process content one step at a time (for large files)
"""
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.content import Content
from app.services.text_extraction_service import TextExtractionService
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
from sqlalchemy import select


async def process_step_by_step():
    """Process content step by step with pauses"""
    
    content_id = "376ecdc0-7639-45ed-9062-bd9d698b760b"
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Content).where(Content.id == content_id)
        )
        content = result.scalar_one()
        
        print(f"\n🚀 Processing: {content.title}\n")
        
        # Step 1: Extract text
        print("📄 Step 1: Extracting text...")
        extraction = TextExtractionService.extract_from_pdf(content.file_path)
        print(f"   ✅ Done: {len(extraction['full_text'])} characters\n")
        
        input("Press Enter to continue to Step 2...")
        
        # Step 2: Create chunks
        print("\n📦 Step 2: Creating chunks...")
        chunks = TextExtractionService.create_chunks(
            text=extraction['full_text'],
            chunk_size=1000,
            chunk_overlap=200,
            metadata={'content_id': str(content.id)}
        )
        print(f"   ✅ Done: {len(chunks)} chunks\n")
        
        input("Press Enter to continue to Step 3...")
        
        # Step 3: Generate embeddings (in batches)
        print("\n🧠 Step 3: Generating embeddings...")
        embedding_service = get_embedding_service()
        
        all_embeddings = []
        batch_size = 100
        
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c['text'] for c in batch]
            embeddings = embedding_service.generate_embeddings(texts)
            all_embeddings.append(embeddings)
            print(f"   ... processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")
        
        import numpy as np
        all_embeddings = np.vstack(all_embeddings)
        print(f"   ✅ Done: {len(all_embeddings)} embeddings\n")
        
        input("Press Enter to continue to Step 4...")
        
        # Step 4: Store in vector DB
        print("\n💾 Step 4: Storing in vector database...")
        vector_store = get_vector_store()
        
        metadata = [{'chunk_index': i, 'text': c['text'], 'content_id': str(content.id)} 
                    for i, c in enumerate(chunks)]
        
        vector_ids = vector_store.add_vectors(all_embeddings, metadata)
        print(f"   ✅ Done: {len(vector_ids)} vectors stored\n")
        
        # Step 5: Update content
        content.processing_status = 'completed'
        content.chunks_count = len(chunks)
        content.embeddings_created = True
        await db.commit()
        
        print("🎉 PROCESSING COMPLETE!\n")


if __name__ == "__main__":
    asyncio.run(process_step_by_step())