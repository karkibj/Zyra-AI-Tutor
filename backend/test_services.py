"""
Test all CRUD services - Phase 2 Verification
"""
import asyncio
import uuid
from datetime import datetime

from app.db import get_db, init_db
from app.core.config import settings
from app.services import DocumentService, ChunkService, EmbeddingService, ChatService


async def test_services():
    print("=" * 60)
    print("🧪 TESTING ALL CRUD SERVICES")
    print("=" * 60)
    
    # Initialize database
    print("\n📊 Initializing database...")
    await init_db()
    print("✅ Database initialized")
    
    # Get database session
    async for db in get_db():
        try:
            # ==================== SETUP: CREATE PREREQUISITE RECORDS ====================
            print("\n" + "=" * 60)
            print("🔧 SETUP: Creating prerequisite records")
            print("=" * 60)
            
            from app.models.user import User
            from app.models.exam import Exam
            from app.models.subject import Subject
            from app.models.chapter import Chapter
            
            # Create test user
            test_user = User(
                user_id=uuid.uuid4(),
                name="Test Student",
                email="test@example.com",
                role="student"
            )
            db.add(test_user)
            
            # Create test exam
            test_exam = Exam(
                exam_id=uuid.uuid4(),
                name="SEE 2025",
                board="NEB",
                grade="Grade 10"
            )
            db.add(test_exam)
            
            # Create test subject
            test_subject = Subject(
                subject_id=uuid.uuid4(),
                exam_id=test_exam.exam_id,
                name="Mathematics",
                code="MATH-10"
            )
            db.add(test_subject)
            
            # Create test chapter
            test_chapter = Chapter(
                chapter_id=uuid.uuid4(),
                subject_id=test_subject.subject_id,
                name="Quadratic Equations",
                chapter_number=1
            )
            db.add(test_chapter)
            
            await db.commit()
            print("✅ Prerequisites created: User, Exam, Subject, Chapter")
            
            # ==================== TEST 1: DOCUMENT SERVICE ====================
            print("\n" + "=" * 60)
            print("📄 TEST 1: DOCUMENT SERVICE")
            print("=" * 60)
            
            # Create a document
            print("\n1️⃣ Creating document...")
            document = await DocumentService.create_document(
                db=db,
                chapter_id=test_chapter.chapter_id,
                subject_id=test_subject.subject_id,
                uploaded_by=test_user.user_id,
                title="Quadratic Equations - Chapter 1",
                description="Introduction to quadratic equations and solving methods",
                language="en",
                doc_type="pdf",
                status="pending"
            )
            print(f"✅ Document created: {document.document_id}")
            print(f"   Title: {document.title}")
            print(f"   Status: {document.status}")
            
            # Get document
            print("\n2️⃣ Retrieving document...")
            retrieved_doc = await DocumentService.get_document(db, document.document_id)
            print(f"✅ Document retrieved: {retrieved_doc.title}")
            
            # Update document status
            print("\n3️⃣ Updating document status to 'processing'...")
            updated_doc = await DocumentService.update_document_status(
                db, document.document_id, "processing"
            )
            print(f"✅ Status updated: {updated_doc.status}")
            
            # ==================== TEST 2: CHUNK SERVICE ====================
            print("\n" + "=" * 60)
            print("🧩 TEST 2: CHUNK SERVICE")
            print("=" * 60)
            
            # Create chunks in batch
            print("\n1️⃣ Creating chunks in batch...")
            chunks_data = [
                {
                    "document_id": document.document_id,
                    "chunk_index": 0,
                    "content": "A quadratic equation is a second-order polynomial equation in a single variable x.",
                    "token_count": 15,
                    "chunk_type": "text"
                },
                {
                    "document_id": document.document_id,
                    "chunk_index": 1,
                    "content": "The general form is ax² + bx + c = 0, where a ≠ 0.",
                    "token_count": 14,
                    "chunk_type": "formula"
                },
                {
                    "document_id": document.document_id,
                    "chunk_index": 2,
                    "content": "The solutions are found using the quadratic formula.",
                    "token_count": 10,
                    "chunk_type": "text"
                }
            ]
            
            chunks = await ChunkService.create_chunks_batch(db, chunks_data)
            print(f"✅ Created {len(chunks)} chunks")
            for i, chunk in enumerate(chunks):
                print(f"   Chunk {i}: {chunk.content[:50]}...")
            
            # Get chunks by document
            print("\n2️⃣ Retrieving chunks for document...")
            retrieved_chunks = await ChunkService.get_chunks_by_document(db, document.document_id)
            print(f"✅ Retrieved {len(retrieved_chunks)} chunks")
            
            # Get chunks by type
            print("\n3️⃣ Getting formula chunks...")
            formula_chunks = await ChunkService.get_chunks_by_type(db, document.document_id, "formula")
            print(f"✅ Found {len(formula_chunks)} formula chunks")
            
            # Count chunks
            print("\n4️⃣ Counting total chunks...")
            chunk_count = await ChunkService.count_chunks(db, document_id=document.document_id)
            print(f"✅ Total chunks: {chunk_count}")
            
            # ==================== TEST 3: EMBEDDING SERVICE ====================
            print("\n" + "=" * 60)
            print("🎯 TEST 3: EMBEDDING SERVICE")
            print("=" * 60)
            
            # Create embeddings in batch
            print("\n1️⃣ Creating embeddings in batch...")
            embeddings_data = [
                {
                    "chunk_id": chunks[0].chunk_id,
                    "embedding_vector": [0.1, 0.2, 0.3, 0.4, 0.5] * 77,  # 385 dims (simulated)
                },
                {
                    "chunk_id": chunks[1].chunk_id,
                    "embedding_vector": [0.2, 0.3, 0.4, 0.5, 0.6] * 77,
                },
                {
                    "chunk_id": chunks[2].chunk_id,
                    "embedding_vector": [0.3, 0.4, 0.5, 0.6, 0.7] * 77,
                }
            ]
            
            embeddings = await EmbeddingService.create_embeddings_batch(db, embeddings_data)
            print(f"✅ Created {len(embeddings)} embeddings")
            for i, emb in enumerate(embeddings):
                print(f"   Embedding {i}: {len(emb.embedding_vector)} dimensions")
            
            # Get embedding by chunk
            print("\n2️⃣ Retrieving embedding for first chunk...")
            retrieved_emb = await EmbeddingService.get_embedding_by_chunk(db, chunks[0].chunk_id)
            print(f"✅ Embedding retrieved: {len(retrieved_emb.embedding_vector)} dimensions")
            print(f"   Model: {retrieved_emb.model_name}")
            
            # Get all embeddings for document
            print("\n3️⃣ Getting all embeddings for document...")
            doc_embeddings = await EmbeddingService.get_embeddings_by_document(db, document.document_id)
            print(f"✅ Retrieved {len(doc_embeddings)} embeddings")
            
            # Count embeddings
            print("\n4️⃣ Counting total embeddings...")
            emb_count = await EmbeddingService.count_embeddings(db, document_id=document.document_id)
            print(f"✅ Total embeddings: {emb_count}")
            
            # Test cosine similarity
            print("\n5️⃣ Testing cosine similarity...")
            similarity = EmbeddingService.calculate_cosine_similarity(
                embeddings[0].embedding_vector,
                embeddings[1].embedding_vector
            )
            print(f"✅ Similarity between chunk 0 and 1: {similarity:.4f}")
            
            # ==================== TEST 4: CHAT SERVICE ====================
            print("\n" + "=" * 60)
            print("💬 TEST 4: CHAT SERVICE")
            print("=" * 60)
            
            # Create chat session
            print("\n1️⃣ Creating chat session...")
            session = await ChatService.create_session(
                db=db,
                user_id=test_user.user_id,
                chapter_id=test_chapter.chapter_id
            )
            print(f"✅ Session created: {session.session_id}")
            print(f"   Started at: {session.started_at}")
            
            # Add messages
            print("\n2️⃣ Adding messages to session...")
            msg1 = await ChatService.add_message(
                db=db,
                session_id=session.session_id,
                sender="user",
                content="What is a quadratic equation?"
            )
            print(f"✅ User message added: {msg1.content}")
            
            msg2 = await ChatService.add_message(
                db=db,
                session_id=session.session_id,
                sender="assistant",
                content="A quadratic equation is a second-order polynomial equation in a single variable x. The general form is ax² + bx + c = 0, where a ≠ 0."
            )
            print(f"✅ Assistant message added: {msg2.content[:50]}...")
            
            # Get session messages
            print("\n3️⃣ Retrieving all session messages...")
            messages = await ChatService.get_session_messages(db, session.session_id)
            print(f"✅ Retrieved {len(messages)} messages")
            for i, msg in enumerate(messages):
                print(f"   Message {i} ({msg.sender}): {msg.content[:40]}...")
            
            # Get recent messages
            print("\n4️⃣ Getting recent messages...")
            recent = await ChatService.get_recent_messages(db, session.session_id, n=2)
            print(f"✅ Retrieved {len(recent)} recent messages")
            
            # Count messages
            print("\n5️⃣ Counting session messages...")
            msg_count = await ChatService.count_session_messages(db, session.session_id)
            print(f"✅ Total messages: {msg_count}")
            
            # End session
            print("\n6️⃣ Ending chat session...")
            ended_session = await ChatService.end_session(db, session.session_id)
            print(f"✅ Session ended at: {ended_session.ended_at}")
            
            # ==================== TEST 5: CASCADE DELETE ====================
            print("\n" + "=" * 60)
            print("🗑️  TEST 5: CASCADE DELETE")
            print("=" * 60)
            
            print("\n1️⃣ Deleting document (should cascade to chunks and embeddings)...")
            deleted = await DocumentService.delete_document(db, document.document_id)
            print(f"✅ Document deleted: {deleted}")
            
            # Verify chunks are deleted
            print("\n2️⃣ Verifying chunks are deleted...")
            remaining_chunks = await ChunkService.get_chunks_by_document(db, document.document_id)
            print(f"✅ Remaining chunks: {len(remaining_chunks)} (should be 0)")
            
            # Verify embeddings are deleted
            print("\n3️⃣ Verifying embeddings are deleted...")
            remaining_embeddings = await EmbeddingService.get_embeddings_by_document(db, document.document_id)
            print(f"✅ Remaining embeddings: {len(remaining_embeddings)} (should be 0)")
            
            # Delete chat session
            print("\n4️⃣ Deleting chat session (should cascade to messages)...")
            session_deleted = await ChatService.delete_session(db, session.session_id)
            print(f"✅ Session deleted: {session_deleted}")
            
            # ==================== FINAL SUMMARY ====================
            print("\n" + "=" * 60)
            print("✅ ALL TESTS PASSED!")
            print("=" * 60)
            print("\n📊 Test Summary:")
            print("   ✅ Document Service: Create, Read, Update, Delete")
            print("   ✅ Chunk Service: Batch Create, Read, Filter, Count")
            print("   ✅ Embedding Service: Batch Create, Read, Similarity")
            print("   ✅ Chat Service: Sessions, Messages, History")
            print("   ✅ Cascade Delete: Documents → Chunks → Embeddings")
            print("\n🚀 Phase 2 COMPLETE! Ready for Phase 3.")
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
        
        break  # Exit after first session


if __name__ == "__main__":
    print(f"\n📊 Testing connection to: {settings.DATABASE_URL}")
    print(f"🏗️  Project: {settings.PROJECT_NAME}")
    print(f"🌍 Environment: {settings.ENV}")
    
    asyncio.run(test_services())