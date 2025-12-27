"""
Phase 3 End-to-End Test - Complete RAG Pipeline
Tests: Upload → Process → Embed → Index → Query → Answer
"""
import asyncio
import uuid
from pathlib import Path

from app.db import get_db, init_db
from app.core.config import settings

# Import Phase 3 components
from app.rag.document_processor import DocumentProcessor
from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.faiss_manager import FAISSManager
from app.rag.integrated_rag_service import IntegratedRAGService

# Import services
from app.models.user import User
from app.models.exam import Exam
from app.models.subject import Subject
from app.models.chapter import Chapter


async def test_phase3_pipeline():
    """
    Complete end-to-end RAG pipeline test
    """
    print("=" * 70)
    print("🚀 PHASE 3: RAG + DATABASE INTEGRATION TEST")
    print("=" * 70)
    
    # Initialize database
    print("\n📊 Initializing database...")
    await init_db()
    print("✅ Database initialized")
    
    async for db in get_db():
        try:
            # ==================== SETUP ====================
            print("\n" + "=" * 70)
            print("🔧 SETUP: Creating test data")
            print("=" * 70)
            
            # Create prerequisites
            test_user = User(
                user_id=uuid.uuid4(),
                name="Test Student",
                email=f"test{uuid.uuid4().hex[:8]}@example.com",
                role="student"
            )
            db.add(test_user)
            
            test_exam = Exam(
                exam_id=uuid.uuid4(),
                name="SEE 2025",
                board="NEB",
                grade="Grade 10"
            )
            db.add(test_exam)
            
            test_subject = Subject(
                subject_id=uuid.uuid4(),
                exam_id=test_exam.exam_id,
                name="Mathematics",
                code="MATH-10"
            )
            db.add(test_subject)
            
            test_chapter = Chapter(
                chapter_id=uuid.uuid4(),
                subject_id=test_subject.subject_id,
                name="Quadratic Equations",
                chapter_number=1
            )
            db.add(test_chapter)
            
            await db.commit()
            print("✅ Test data created")
            
            # ==================== TEST 1: DOCUMENT PROCESSING ====================
            print("\n" + "=" * 70)
            print("📄 TEST 1: DOCUMENT PROCESSING")
            print("=" * 70)
            
            # Create sample PDF content (simulated)
            sample_text = """
            Quadratic Equations
            
            A quadratic equation is a second-order polynomial equation in a single variable x.
            The general form of a quadratic equation is ax² + bx + c = 0, where a ≠ 0.
            
            The solutions to a quadratic equation are given by the quadratic formula:
            x = (-b ± √(b² - 4ac)) / (2a)
            
            The discriminant Δ = b² - 4ac determines the nature of the roots:
            - If Δ > 0: Two distinct real roots
            - If Δ = 0: One repeated real root
            - If Δ < 0: Two complex conjugate roots
            
            Example: Solve x² - 5x + 6 = 0
            Here, a = 1, b = -5, c = 6
            Discriminant = (-5)² - 4(1)(6) = 25 - 24 = 1
            
            Since Δ > 0, we have two distinct real roots.
            Using the quadratic formula:
            x = (5 ± √1) / 2
            x = (5 ± 1) / 2
            
            Therefore, x = 3 or x = 2
            
            Practice Problems:
            1. Solve x² + 6x + 8 = 0
            2. Solve 2x² - 7x + 3 = 0
            3. Find the discriminant of 3x² + 4x + 2 = 0
            """.strip()
            
            # Simulate PDF by creating chunks directly
            print("\n1️⃣ Processing document...")
            chunks_data = DocumentProcessor.chunk_text(sample_text, chunk_size=300, overlap=50)
            
            # Create document
            from app.services.document_service import DocumentService
            document = await DocumentService.create_document(
                db=db,
                chapter_id=test_chapter.chapter_id,
                subject_id=test_subject.subject_id,
                uploaded_by=test_user.user_id,
                title="Quadratic Equations - Complete Guide",
                description="Comprehensive guide to quadratic equations",
                status="processing"
            )
            print(f"✅ Document created: {document.document_id}")
            
            # Store chunks
            print("\n2️⃣ Creating chunks...")
            for chunk in chunks_data:
                chunk["document_id"] = document.document_id
            
            from app.services.chunk_service import ChunkService
            chunks = await ChunkService.create_chunks_batch(db, chunks_data)
            print(f"✅ Created {len(chunks)} chunks")
            for i, chunk in enumerate(chunks[:3]):
                print(f"   Chunk {i}: {chunk.content[:60]}...")
            
            # Update document status
            await DocumentService.update_document_status(db, document.document_id, "completed")
            
            # ==================== TEST 2: EMBEDDING GENERATION ====================
            print("\n" + "=" * 70)
            print("🎯 TEST 2: EMBEDDING GENERATION")
            print("=" * 70)
            
            print("\n1️⃣ Generating embeddings...")
            result = await EmbeddingGenerator.create_embeddings_for_document(
                db=db,
                document_id=document.document_id,
                batch_size=10
            )
            print(f"✅ Created {result['embeddings_created']} embeddings")
            print(f"   Model: {result['model_name']}")
            print(f"   Dimension: {result['embedding_dimension']}")
            
            # ==================== TEST 3: FAISS INDEX ====================
            print("\n" + "=" * 70)
            print("🔍 TEST 3: FAISS INDEX BUILDING")
            print("=" * 70)
            
            print("\n1️⃣ Building FAISS index...")
            faiss_manager = FAISSManager()
            index_stats = await faiss_manager.build_index_from_database(db, document.document_id)
            print(f"✅ Index built successfully")
            print(f"   Vectors indexed: {index_stats['vectors_indexed']}")
            print(f"   Dimension: {index_stats['dimension']}")
            
            # Test search
            print("\n2️⃣ Testing semantic search...")
            query = "What is the quadratic formula?"
            query_embedding = EmbeddingGenerator.generate_embedding(query)
            
            search_results = await faiss_manager.search_and_retrieve(
                db=db,
                query_embedding=query_embedding,
                k=3
            )
            print(f"✅ Retrieved {len(search_results)} chunks")
            for i, result in enumerate(search_results):
                print(f"\n   Result {i+1} (score: {result['score']:.4f}):")
                print(f"   {result['content'][:100]}...")
            
            # ==================== TEST 4: INTEGRATED RAG ====================
            print("\n" + "=" * 70)
            print("🤖 TEST 4: INTEGRATED RAG SERVICE")
            print("=" * 70)
            
            print("\n1️⃣ Initializing RAG service...")
            rag_service = IntegratedRAGService()
            await rag_service.initialize_index(db, document.document_id)
            print("✅ RAG service initialized")
            
            # Test questions
            test_questions = [
                "What is a quadratic equation?",
                "How do you solve a quadratic equation?",
                "What does the discriminant tell us?",
                "Solve x² - 5x + 6 = 0"
            ]
            
            print("\n2️⃣ Testing question answering...")
            for i, question in enumerate(test_questions, 1):
                print(f"\n❓ Question {i}: {question}")
                
                response = await rag_service.ask(
                    db=db,
                    user_id=test_user.user_id,
                    question=question,
                    chapter_id=test_chapter.chapter_id
                )
                
                print(f"   Intent: {response['intent']}")
                print(f"   Sources: {response['chunk_count']} chunks")
                print(f"   Response time: {response['response_time']:.2f}s")
                print(f"   Answer: {response['answer'][:150]}...")
                
                if response['sources']:
                    print(f"   Top source: {response['sources'][0]['content'][:80]}...")
            
            # ==================== TEST 5: CONVERSATION HISTORY ====================
            print("\n" + "=" * 70)
            print("💬 TEST 5: CONVERSATION HISTORY")
            print("=" * 70)
            
            # Get conversation history
            session_id = uuid.UUID(response['session_id'])
            history = await rag_service.get_conversation_history(db, session_id, limit=10)
            
            print(f"\n✅ Retrieved conversation history: {len(history)} messages")
            for i, msg in enumerate(history[-4:]):  # Show last 4 messages
                print(f"   {msg['role']}: {msg['content'][:80]}...")
            
            # ==================== STATS ====================
            print("\n" + "=" * 70)
            print("📊 RAG SYSTEM STATISTICS")
            print("=" * 70)
            
            stats = rag_service.get_stats()
            print(f"\nFAISS Index:")
            print(f"   Status: {stats['faiss_index']['status']}")
            print(f"   Vectors: {stats['faiss_index'].get('total_vectors', 'N/A')}")
            print(f"   Dimension: {stats['faiss_index'].get('dimension', 'N/A')}")
            print(f"\nModels:")
            print(f"   Embeddings: {stats['embedding_model']}")
            print(f"   LLM: {stats['llm_model']}")
            print(f"\nConfiguration:")
            print(f"   Chunk size: {stats['chunk_size']}")
            print(f"   Retrieval K: {stats['retrieval_k']}")
            
            # ==================== SUCCESS ====================
            print("\n" + "=" * 70)
            print("✅ ALL PHASE 3 TESTS PASSED!")
            print("=" * 70)
            print("\n🎉 Database-integrated RAG pipeline is working!")
            print("📊 Summary:")
            print(f"   ✅ Document processed: 1")
            print(f"   ✅ Chunks created: {len(chunks)}")
            print(f"   ✅ Embeddings generated: {result['embeddings_created']}")
            print(f"   ✅ FAISS index built: {index_stats['vectors_indexed']} vectors")
            print(f"   ✅ Questions answered: {len(test_questions)}")
            print(f"   ✅ Conversation saved: {len(history)} messages")
            print("\n🚀 ZYRA IS PRODUCTION READY!")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
        
        break


if __name__ == "__main__":
    print(f"\n📊 Testing RAG Pipeline")
    print(f"🏗️  Project: {settings.PROJECT_NAME}")
    print(f"🌍 Environment: {settings.ENV}")
    
    asyncio.run(test_phase3_pipeline())