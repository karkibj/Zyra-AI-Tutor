"""
Automatic content processor - runs continuously in background
Run this: python -m workers.auto_processor

Processes pending uploads automatically using the proper pipeline.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import re
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


# ── Chapter keyword detection (for model question tagging) ───────────────────
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
    'Algebraic Fraction': ['simplify', 'algebraic', 'fraction', '4^x'],
    'Indices': ['indices', 'exponent', '1/x + 1/y', 'laws of indices'],
    'Triangles and Quadrilaterals': ['triangle', 'quadrilateral', 'parallel',
                                      'prove that', 'area of triangle'],
    'Construction': ['construct', 'compass', 'ruler', 'AB = BC'],
    'Circle': ['circle', 'chord', 'tangent', 'arc', 'cyclic', 'inscribed',
               'opposite angles'],
    'Statistics': ['mean', 'median', 'mode', 'frequency', 'quartile',
                    'standard deviation', 'class interval'],
    'Probability': ['probability', 'sample space', 'event', 'dice', 'coin',
                     'ball', 'favorable', 'tree diagram'],
    'Trigonometry': ['sin', 'cos', 'tan', 'angle of elevation', 'angle of depression',
                      'height', 'pole', 'tower', 'kite'],
}


def detect_chapter(text: str):
    text_lower = text.lower()
    scores = {ch: sum(1 for kw in kws if kw.lower() in text_lower)
              for ch, kws in CHAPTER_KEYWORDS.items()}
    scores = {k: v for k, v in scores.items() if v > 0}
    return max(scores, key=scores.get) if scores else None


def chunk_model_questions(text: str, content_id: str, title: str, content_type: str) -> list:
    """Question-level chunking for model questions with chapter tagging."""
    question_pattern = re.compile(r'(?:^|\n)(?:Q\.?\s*)?(\d{1,2})(?:\.)\s', re.MULTILINE)
    boundaries = [m.start() for m in question_pattern.finditer(text)]

    base_meta = {'content_id': content_id, 'title': title, 'content_type': content_type}

    if len(boundaries) < 2:
        # Fallback to 800-char chunks
        chunks = []
        i = 0
        while i < len(text):
            chunk = text[i:i+800].strip()
            if chunk:
                meta = dict(base_meta)
                meta.update({'chunk_index': len(chunks), 'text': chunk,
                             'chapter': detect_chapter(chunk)})
                chunks.append(meta)
            i += 700
        return chunks

    chunks = []
    for i, start in enumerate(boundaries):
        end = boundaries[i+1] if i+1 < len(boundaries) else len(text)
        q_text = text[start:end].strip()
        if len(q_text) < 30:
            continue
        meta = dict(base_meta)
        meta.update({
            'chunk_index': i,
            'text': q_text,          # ← FULL TEXT, no truncation
            'chapter': detect_chapter(q_text),
        })
        chunks.append(meta)
    return chunks


def safe_chunk_text(text, content_id, title, content_type, chunk_size=800, overlap=100):
    """Standard chunking for curriculum/past_paper content."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text) and len(chunks) < 10000:
        chunk = text[start:start+chunk_size].strip()
        if chunk:
            chunks.append({
                'content_id': content_id,
                'title': title,
                'content_type': content_type,
                'chunk_index': len(chunks),
                'text': chunk,         # ← FULL TEXT, no truncation
                'chapter': None,
            })
        start += (chunk_size - overlap)
    return chunks


async def process_one_task(task, db):
    """Process a single queue task."""
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    print(f"\n{'='*60}")
    print(f"Processing task: {task.id}")

    try:
        content_result = await db.execute(
            select(Content).where(Content.id == task.content_id)
        )
        content = content_result.scalar_one_or_none()

        if not content:
            task.status = "failed"
            task.error_message = "Content not found"
            await db.commit()
            return False

        print(f"  Title: {content.title}")
        print(f"  Type:  {content.content_type}")

        task.status = "processing"
        task.started_at = datetime.utcnow()
        content.processing_status = "processing"
        await db.commit()

        # Extract text
        print("  Extracting text...")
        doc = fitz.open(content.file_path)
        total_pages = len(doc)
        all_text = "".join(doc[p].get_text() + "\n" for p in range(total_pages))
        doc.close()
        print(f"  Pages: {total_pages}, Chars: {len(all_text):,}")

        # Chunk — question-level for model questions, standard for everything else
        print("  Creating chunks...")
        content_id_str = str(content.id)

        if content.content_type == 'model_question':
            chunk_metadata = chunk_model_questions(
                all_text, content_id_str, content.title, content.content_type
            )
            print(f"  Question-level chunks: {len(chunk_metadata)} (chapter-tagged)")
        else:
            chunk_metadata = safe_chunk_text(
                all_text, content_id_str, content.title, content.content_type
            )
            print(f"  Standard chunks: {len(chunk_metadata)}")

        if not chunk_metadata:
            raise Exception("No chunks created — PDF may be empty or scanned")

        # Generate embeddings and store
        print("  Generating embeddings...")
        batch_size = 50
        total_added = 0

        for i in range(0, len(chunk_metadata), batch_size):
            batch = chunk_metadata[i:i+batch_size]
            texts = [m['text'] for m in batch]
            embeddings = np.array(
                [embedding_service.generate_embedding(t) for t in texts],
                dtype='float32'
            )
            vector_store.add_vectors(embeddings, batch)
            total_added += len(batch)
            task.progress = (total_added / len(chunk_metadata)) * 100
            await db.commit()

        print(f"  Stored {total_added} vectors")

        # Update content record
        content.processing_status = "completed"
        content.chunks_count = len(chunk_metadata)
        content.embeddings_created = True
        content.page_count = total_pages

        task.status = "completed"
        task.progress = 100.0
        task.completed_at = datetime.utcnow()
        task.result = {
            "chunks_created": len(chunk_metadata),
            "pages_processed": total_pages
        }

        await db.commit()
        print(f"  COMPLETED!")
        return True

    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        task.status = "failed"
        task.error_message = str(e)
        task.attempts += 1
        task.completed_at = datetime.utcnow()
        content.processing_status = "failed"
        await db.commit()
        return False


async def process_pending_queue():
    """Process all pending items in queue."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ProcessingQueue)
            .where(ProcessingQueue.status == "pending")
            .order_by(ProcessingQueue.priority.desc())
        )
        pending_tasks = result.scalars().all()

        if not pending_tasks:
            return 0

        print(f"\nFound {len(pending_tasks)} pending task(s)")
        processed = 0
        for task in pending_tasks:
            if await process_one_task(task, db):
                processed += 1
        return processed


async def worker_loop():
    """Main worker loop — runs continuously."""
    print("="*60)
    print("AUTOMATIC CONTENT PROCESSOR STARTED")
    print("="*60)
    print("Checking queue every 30 seconds. Press Ctrl+C to stop.")
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
                    stats = get_vector_store().get_stats()
                    print(f"Processed {processed} item(s). Total vectors: {stats['total_vectors']:,}")
                else:
                    print("No pending tasks.")
            except Exception as e:
                print(f"Worker error: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\nWORKER STOPPED.")


if __name__ == "__main__":
    asyncio.run(worker_loop())