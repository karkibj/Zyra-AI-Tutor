"""
Process existing CDC - Works with your TextExtractionService
Extracts all at once, then chunks in batches
"""
import asyncio
import sys
from pathlib import Path
import gc

sys.path.append(str(Path(__file__).parent.parent))

from app.db import AsyncSessionLocal
from app.models.content import Content
from app.services.text_extraction_service import TextExtractionService
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store
from sqlalchemy import select
import uuid


async def process_cdc_simple():
    """Process CDC using existing TextExtractionService"""
    
    print("\n" + "="*70)
    print("🎓 PROCESSING EXISTING CDC CURRICULUM")
    print("="*70 + "\n")
    
    async with AsyncSessionLocal() as db:
        # Find CDC
        print("🔍 Looking for CDC content...")
        
        result = await db.execute(
            select(Content).where(
                Content.title.contains("CDC"),
                Content.content_type == "curriculum"
            )
        )
        content = result.scalars().first()
        
        if not content:
            print("❌ CDC not found!")
            return
        
        print(f"✅ Found: {content.title}")
        print(f"   ID: {content.id}")
        print(f"   File: {content.file_path}")
        print(f"   Status: {content.processing_status}")
        
        # Find file
        file_path = Path(content.file_path)
        if not file_path.exists():
            file_path = Path("/mnt/project/cdc.pdf")
            if not file_path.exists():
                print("❌ File not found!")
                return
        
        print(f"   Size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        if content.processing_status == "completed":
            print("\n⚠️  Already processed!")
            if input("   Re-process? (yes/no): ").lower() != 'yes':
                return
        
        print("\n" + "="*70)
        print("⚠️  WARNING: This will extract ALL 310 pages!")
        print("   Your device may lag for 2-3 minutes")
        print("   Keep it plugged in and don't touch it")
        print("="*70)
        
        input("\n⏸️  Press ENTER to start (or Ctrl+C to cancel)...")
        
        # STEP 1: Extract ALL text
        print("\n📄 STEP 1: EXTRACTING TEXT FROM PDF")
        print("="*70)
        print("📖 Extracting all 310 pages... (this will take 2-3 minutes)")
        print("   ⏳ Please wait, don't touch your device...\n")
        
        try:
            extraction = TextExtractionService.extract_from_pdf(str(file_path))
            full_text = extraction['full_text']
            total_pages = extraction['total_pages']
            
            print(f"\n✅ STEP 1 COMPLETE!")
            print(f"   Pages: {total_pages}")
            print(f"   Characters: {len(full_text):,}")
            print(f"   Estimated tokens: {len(full_text) // 4:,}")
            
        except Exception as e:
            print(f"\n❌ Extraction failed: {e}")
            return
        
        input("\n⏸️  Press ENTER to continue to chunking...")
        
        # STEP 2: Create chunks in BATCHES
        print("\n📦 STEP 2: CREATING TEXT CHUNKS")
        print("="*70)
        print("🔄 Chunking text in 50,000 character batches...")
        print("   (Prevents memory overflow)\n")
        
        all_chunks = []
        batch_size = 50000  # Process 50k chars at a time
        
        for i in range(0, len(full_text), batch_size):
            batch_text = full_text[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(full_text) + batch_size - 1) // batch_size
            
            print(f"   Batch {batch_num}/{total_batches}...", end=" ", flush=True)
            
            batch_chunks = TextExtractionService.create_chunks(
                batch_text,
                chunk_size=800,
                chunk_overlap=100,
                metadata={'content_id': str(content.id)}
            )
            
            all_chunks.extend(batch_chunks)
            print(f"✓ {len(batch_chunks)} chunks")
            
            gc.collect()
            await asyncio.sleep(0.2)
        
        print(f"\n✅ STEP 2 COMPLETE: {len(all_chunks)} chunks created")
        
        input("\n⏸️  Press ENTER to continue to embeddings...")
        
        # STEP 3: Generate embeddings
        print("\n🧠 STEP 3: GENERATING EMBEDDINGS")
        print("="*70)
        print(f"📊 Creating embeddings for {len(all_chunks)} chunks")
        print("🔄 Processing in batches of 20...\n")
        
        embedding_service = get_embedding_service()
        vector_store = get_vector_store()
        
        embed_batch_size = 20
        total_batches = (len(all_chunks) + embed_batch_size - 1) // embed_batch_size
        
        for i in range(0, len(all_chunks), embed_batch_size):
            batch = all_chunks[i:i + embed_batch_size]
            batch_num = (i // embed_batch_size) + 1
            
            print(f"   Batch {batch_num}/{total_batches} ({len(batch)} chunks)...", end=" ", flush=True)
            
            # Get texts
            texts = [chunk['text'] for chunk in batch]
            
            # Generate embeddings
            embeddings = embedding_service.generate_embeddings(texts)
            
            # Store in vector DB
            for j, chunk in enumerate(batch):
                vector_store.add_vector(
                    vector_id=str(uuid.uuid4()),
                    embedding=embeddings[j],
                    metadata={
                        'content_id': str(content.id),
                        'text': chunk['text'],
                        'chunk_index': i + j,
                        'source': 'cdc_curriculum',
                        'title': content.title
                    }
                )
            
            print("✓")
            gc.collect()
            await asyncio.sleep(0.5)
        
        # Save vector store
        vector_store.save()
        
        print(f"\n✅ STEP 3 COMPLETE: {len(all_chunks)} embeddings saved")
        
        # STEP 4: Update database
        print("\n💾 STEP 4: UPDATING DATABASE")
        print("="*70)
        
        content.processing_status = "completed"
        content.chunks_count = len(all_chunks)
        content.embeddings_created = True
        content.metadata = {
            **content.metadata,
            "processing_complete": True,
            "chunk_size": 800,
            "chunk_overlap": 100
        }
        
        await db.commit()
        
        print("✅ Database updated")
        
        # FINAL STATS
        print("\n" + "="*70)
        print("🎉 CDC PROCESSING COMPLETE!")
        print("="*70)
        print(f"📄 Pages: {total_pages}")
        print(f"📦 Chunks: {len(all_chunks)}")
        print(f"🧠 Embeddings: {len(all_chunks)}")
        print(f"💾 Status: {content.processing_status}")
        print("="*70)
        print()
        print("✅ CDC is now ready for student questions!")
        print("💬 Students can ask about any math topic")
        print()


if __name__ == "__main__":
    print("\n🚀 CDC Processing Script")
    print("⏱️  Total time: ~15-20 minutes")
    print("💻 Keep device plugged in and don't use it during processing\n")
    
    try:
        asyncio.run(process_cdc_simple())
        print("✅ Processing completed successfully!\n")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()