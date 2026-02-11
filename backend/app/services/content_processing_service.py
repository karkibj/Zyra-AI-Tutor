"""
Content Processing Service
Orchestrates text extraction, chunking, and embedding generation
Integrates with processing_queue for background tasks
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, List
import asyncio
from datetime import datetime

from app.models.content import Content
from app.models.processing_queue import ProcessingQueue
from app.models.extracted_item import ExtractedItem
from app.services.text_extraction_service import TextExtractionService
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store


class ContentProcessingService:
    """Process uploaded content: extract text, generate embeddings, store in vector DB"""
    
    @staticmethod
    async def process_content(content_id: str, db: AsyncSession) -> Dict:
        """
        Main processing pipeline for content
        
        Steps:
        1. Extract text from PDF
        2. Create intelligent chunks
        3. Generate embeddings
        4. Store in vector database
        5. Extract questions (if past paper)
        6. Update content status
        
        Args:
            content_id: UUID of content to process
            db: Database session
            
        Returns:
            Processing results dictionary
        """
        try:
            # Get content
            result = await db.execute(
                select(Content).where(Content.id == content_id)
            )
            content = result.scalar_one_or_none()
            
            if not content:
                raise ValueError(f"Content {content_id} not found")
            
            print(f"\n{'='*60}")
            print(f"🚀 Processing: {content.title}")
            print(f"   Type: {content.content_type}")
            print(f"   File: {content.file_path}")
            print(f"{'='*60}\n")
            
            # Step 1: Extract text from PDF
            print("📄 Step 1: Extracting text from PDF...")
            extraction_result = TextExtractionService.extract_from_pdf(content.file_path)
            
            full_text = extraction_result['full_text']
            total_pages = extraction_result['total_pages']
            
            print(f"   ✅ Extracted {len(full_text)} characters from {total_pages} pages")
            
            # Step 2: Create chunks
            print("\n📦 Step 2: Creating text chunks...")
            chunks = TextExtractionService.create_chunks(
                text=full_text,
                chunk_size=1000,
                chunk_overlap=200,
                metadata={
                    'content_id': str(content.id),
                    'title': content.title,
                    'content_type': content.content_type,
                    'source': content.file_path
                }
            )
            
            print(f"   ✅ Created {len(chunks)} chunks")
            
            # Step 3: Generate embeddings
            print("\n🧠 Step 3: Generating embeddings...")
            embedding_service = get_embedding_service()
            
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = embedding_service.generate_embeddings(chunk_texts)
            
            print(f"   ✅ Generated {len(embeddings)} embeddings (dim={embeddings.shape[1]})")
            
            # Step 4: Store in vector database
            print("\n💾 Step 4: Storing in vector database...")
            vector_store = get_vector_store()
            
            # Prepare metadata for vector store
            vector_metadata = []
            for i, chunk in enumerate(chunks):
                meta = chunk['metadata'].copy()
                meta.update({
                    'chunk_index': chunk['chunk_index'],
                    'text': chunk['text'],
                    'char_count': chunk['char_count']
                })
                vector_metadata.append(meta)
            
            vector_ids = vector_store.add_vectors(embeddings, vector_metadata)
            
            print(f"   ✅ Stored {len(vector_ids)} vectors in FAISS")
            
            # Step 5: Extract questions (for past papers and model questions)
            extracted_questions = 0
            if content.content_type in ['past_paper', 'model_question']:
                print("\n❓ Step 5: Extracting questions...")
                questions = TextExtractionService.extract_questions_from_text(full_text)
                
                for question in questions:
                    item = ExtractedItem(
                        content_id=content.id,
                        item_type='question',
                        item_number=question['question_number'],
                        text=question['text'],
                        metadata={
                            'source': content.title,
                            'extraction_method': 'pattern_matching'
                        }
                    )
                    db.add(item)
                
                extracted_questions = len(questions)
                print(f"   ✅ Extracted {extracted_questions} questions")
            
            # Step 6: Update content record
            print("\n✨ Step 6: Updating content record...")
            content.processing_status = 'completed'
            content.chunks_count = len(chunks)
            content.embeddings_created = True
            content.vector_store_id = f"faiss_{content_id}"
            
            # Update metadata
            if content.metadata is None:
                content.metadata = {}
            content.metadata.update({
                'processed_at': datetime.utcnow().isoformat(),
                'total_chunks': len(chunks),
                'embedding_dimension': int(embeddings.shape[1]),
                'extracted_questions': extracted_questions,
                'char_count': len(full_text)
            })
            
            await db.commit()
            
            print(f"\n{'='*60}")
            print("🎉 PROCESSING COMPLETE!")
            print(f"   Chunks: {len(chunks)}")
            print(f"   Embeddings: {len(embeddings)}")
            print(f"   Questions: {extracted_questions}")
            print(f"   Status: ✅ {content.processing_status}")
            print(f"{'='*60}\n")
            
            return {
                'success': True,
                'content_id': str(content.id),
                'chunks_created': len(chunks),
                'embeddings_created': len(embeddings),
                'questions_extracted': extracted_questions,
                'status': 'completed'
            }
            
        except Exception as e:
            # Mark as failed
            await db.execute(
                update(Content)
                .where(Content.id == content_id)
                .values(processing_status='failed')
            )
            await db.commit()
            
            print(f"\n❌ PROCESSING FAILED: {str(e)}\n")
            
            return {
                'success': False,
                'content_id': str(content_id),
                'error': str(e),
                'status': 'failed'
            }
    
    @staticmethod
    async def process_queue_item(queue_id: str, db: AsyncSession) -> Dict:
        """
        Process a single item from processing queue
        
        Args:
            queue_id: UUID of queue item
            db: Database session
            
        Returns:
            Processing results
        """
        # Get queue item
        result = await db.execute(
            select(ProcessingQueue).where(ProcessingQueue.id == queue_id)
        )
        queue_item = result.scalar_one_or_none()
        
        if not queue_item:
            return {'success': False, 'error': 'Queue item not found'}
        
        # Update status to processing
        queue_item.status = 'processing'
        queue_item.started_at = datetime.utcnow()
        queue_item.attempts += 1
        await db.commit()
        
        # Process based on task type
        if queue_item.task_type == 'extract_text':
            result = await ContentProcessingService.process_content(
                str(queue_item.content_id),
                db
            )
        else:
            result = {
                'success': False,
                'error': f'Unknown task type: {queue_item.task_type}'
            }
        
        # Update queue item
        if result['success']:
            queue_item.status = 'completed'
            queue_item.progress = 100.0
            queue_item.result = result
        else:
            # Check if should retry
            if queue_item.attempts < queue_item.max_attempts:
                queue_item.status = 'pending'  # Will retry
            else:
                queue_item.status = 'failed'
            queue_item.error_message = result.get('error', 'Unknown error')
        
        queue_item.completed_at = datetime.utcnow()
        await db.commit()
        
        return result