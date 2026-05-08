"""
Content Processing Service
Orchestrates text extraction, chunking, and embedding generation
Integrates with processing_queue for background tasks
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Dict, List
import asyncio
import re
from datetime import datetime

from app.models.content import Content
from app.models.processing_queue import ProcessingQueue
from app.models.extracted_item import ExtractedItem
from app.services.text_extraction_service import TextExtractionService
from app.services.embedding_service import get_embedding_service
from app.services.vector_store_service import get_vector_store


# ============================================================================
# QUESTION-LEVEL CHUNKER FOR MODEL QUESTIONS
# Only used when content_type == 'model_question'
# ============================================================================

def _chunk_model_questions(text: str, base_metadata: dict) -> list:
    """
    Question-level chunking for SEE model question PDFs.
    Splits at question boundaries (1., 2., Q1. etc).
    Tags each chunk with CDC chapter using keyword detection.
    """

    CHAPTER_KEYWORDS = {
        'Sets': ['union', 'intersection', 'venn', 'n(', 'cardinality', 'subset',
                 'universal set', 'complement', 'iphone', 'android', 'survey'],
        'Compound Interest': ['compound interest', 'principal', 'half-yearly',
                               'semi-annual', 'deposited', 'bank', 'CI', 'CA'],
        'Growth and Depreciation': ['depreciation', 'growth', 'population',
                                     'minibus', 'vehicle', 'rate of depreciation'],
        'Currency and Exchange Rate': ['exchange rate', 'dollar', 'currency',
                                        'pound', 'buying rate', 'selling rate', 'devaluation'],
        'Area and Volume': ['volume', 'surface area', 'cone', 'cylinder', 'sphere',
                             'hemisphere', 'pyramid', 'prism', 'frustum', 'slant height'],
        'Sequence and Series': ['arithmetic', 'geometric', 'sequence', 'series',
                                 'common difference', 'common ratio', 'nth term', 'means'],
        'Quadratic Equation': ['quadratic', 'roots', 'discriminant', 'factorization',
                                'ax2', 'ax^2', 'perimeter', 'rectangular'],
        'Algebraic Fraction': ['simplify', 'algebraic', 'fraction', '4^x', 'solve'],
        'Indices': ['indices', 'exponent', '1/x + 1/y', 'laws of indices', 'prove that'],
        'Triangles and Quadrilaterals': ['triangle', 'quadrilateral', 'parallel',
                                          'prove that', 'area of triangle', 'parallelogram'],
        'Construction': ['construct', 'compass', 'ruler', 'AB = BC', 'quadrilateral ABCD'],
        'Circle': ['circle', 'chord', 'tangent', 'arc', 'cyclic', 'inscribed',
                   'opposite angles', 'cyclic quadrilateral'],
        'Statistics': ['mean', 'median', 'mode', 'frequency', 'quartile',
                        'standard deviation', 'class interval', 'cumulative frequency'],
        'Probability': ['probability', 'sample space', 'event', 'dice', 'coin',
                         'ball', 'favorable', 'tree diagram', 'outcomes'],
        'Trigonometry': ['sin', 'cos', 'tan', 'angle of elevation', 'angle of depression',
                          'height', 'pole', 'tower', 'kite', 'string'],
    }

    def detect_chapter(text: str) -> str | None:
        text_lower = text.lower()
        scores = {}
        for chapter, keywords in CHAPTER_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                scores[chapter] = score
        return max(scores, key=scores.get) if scores else None

    # Split on question boundaries: "1.", "2.", "Q1.", etc at line start
    question_pattern = re.compile(
        r'(?:^|\n)(?:Q\.?\s*)?(\d{1,2})(?:\.|\.)\s',
        re.MULTILINE
    )
    boundaries = [m.start() for m in question_pattern.finditer(text)]

    chunks = []

    if len(boundaries) < 2:
        # Fallback: 800-char chunks if question detection fails
        i, chunk_idx = 0, 0
        while i < len(text):
            chunk_text = text[i:i+800].strip()
            if chunk_text:
                meta = dict(base_metadata)
                meta.update({
                    'chunk_index': chunk_idx,
                    'text': chunk_text,
                    'char_count': len(chunk_text),
                    'chapter': detect_chapter(chunk_text),
                })
                chunks.append({'text': chunk_text, 'chunk_index': chunk_idx,
                                'char_count': len(chunk_text), 'metadata': meta})
                chunk_idx += 1
            i += 700
        return chunks

    # One chunk per question
    for i, start in enumerate(boundaries):
        end = boundaries[i + 1] if i + 1 < len(boundaries) else len(text)
        question_text = text[start:end].strip()
        if len(question_text) < 30:
            continue
        meta = dict(base_metadata)
        meta.update({
            'chunk_index': i,
            'text': question_text,
            'char_count': len(question_text),
            'chapter': detect_chapter(question_text),
        })
        chunks.append({'text': question_text, 'chunk_index': i,
                       'char_count': len(question_text), 'metadata': meta})

    return chunks


# ============================================================================
# MAIN SERVICE — unchanged from original except Step 2 branch
# ============================================================================

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
        """
        try:
            result = await db.execute(
                select(Content).where(Content.id == content_id)
            )
            content = result.scalar_one_or_none()

            if not content:
                raise ValueError(f"Content {content_id} not found")

            print(f"\n{'='*60}")
            print(f"Processing: {content.title}")
            print(f"   Type: {content.content_type}")
            print(f"   File: {content.file_path}")
            print(f"{'='*60}\n")

            # Step 1: Extract text from PDF
            print("Step 1: Extracting text from PDF...")
            extraction_result = TextExtractionService.extract_from_pdf(content.file_path)
            full_text = extraction_result['full_text']
            total_pages = extraction_result['total_pages']
            print(f"   Extracted {len(full_text)} characters from {total_pages} pages")

            # Step 2: Create chunks
            print("\nStep 2: Creating text chunks...")
            base_metadata = {
                'content_id': str(content.id),
                'title': content.title,
                'content_type': content.content_type,
                'source': content.file_path
            }

            # Model questions: question-level chunking + chapter tagging
            if content.content_type == 'model_question':
                chunks = _chunk_model_questions(full_text, base_metadata)
                print(f"   Created {len(chunks)} question-level chunks (chapter-tagged)")
            else:
                chunks = TextExtractionService.create_chunks(
                    text=full_text,
                    chunk_size=1000,
                    chunk_overlap=200,
                    metadata=base_metadata
                )
                print(f"   Created {len(chunks)} chunks")

            # Step 3: Generate embeddings
            print("\nStep 3: Generating embeddings...")
            embedding_service = get_embedding_service()
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = embedding_service.generate_embeddings(chunk_texts)
            print(f"   Generated {len(embeddings)} embeddings (dim={embeddings.shape[1]})")

            # Step 4: Store in vector database
            print("\nStep 4: Storing in vector database...")
            vector_store = get_vector_store()
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
            print(f"   Stored {len(vector_ids)} vectors in FAISS")

            # Step 5: Extract questions (for past papers and model questions)
            extracted_questions = 0
            if content.content_type in ['past_paper', 'model_question']:
                print("\nStep 5: Extracting questions...")
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
                print(f"   Extracted {extracted_questions} questions")

            # Step 6: Update content record
            print("\nStep 6: Updating content record...")
            content.processing_status = 'completed'
            content.chunks_count = len(chunks)
            content.embeddings_created = True
            content.vector_store_id = f"faiss_{content_id}"

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
            print("PROCESSING COMPLETE!")
            print(f"   Chunks: {len(chunks)}")
            print(f"   Embeddings: {len(embeddings)}")
            print(f"   Questions: {extracted_questions}")
            print(f"   Status: completed")
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
            await db.execute(
                update(Content)
                .where(Content.id == content_id)
                .values(processing_status='failed')
            )
            await db.commit()
            print(f"\nPROCESSING FAILED: {str(e)}\n")
            return {
                'success': False,
                'content_id': str(content_id),
                'error': str(e),
                'status': 'failed'
            }

    @staticmethod
    async def process_queue_item(queue_id: str, db: AsyncSession) -> Dict:
        """Process a single item from processing queue"""
        result = await db.execute(
            select(ProcessingQueue).where(ProcessingQueue.id == queue_id)
        )
        queue_item = result.scalar_one_or_none()

        if not queue_item:
            return {'success': False, 'error': 'Queue item not found'}

        queue_item.status = 'processing'
        queue_item.started_at = datetime.utcnow()
        queue_item.attempts += 1
        await db.commit()

        if queue_item.task_type == 'extract_text':
            result = await ContentProcessingService.process_content(
                str(queue_item.content_id), db
            )
        else:
            result = {'success': False, 'error': f'Unknown task type: {queue_item.task_type}'}

        if result['success']:
            queue_item.status = 'completed'
            queue_item.progress = 100.0
            queue_item.result = result
        else:
            queue_item.status = 'pending' if queue_item.attempts < queue_item.max_attempts else 'failed'
            queue_item.error_message = result.get('error', 'Unknown error')

        queue_item.completed_at = datetime.utcnow()
        await db.commit()
        return result