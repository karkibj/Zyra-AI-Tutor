"""
Integrated RAG Service - Combines all components for question answering
"""
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from langchain_core.documents import Document

from app.rag.embedding_generator import EmbeddingGenerator
from app.rag.faiss_manager import FAISSManager
from app.services.chat_service import ChatService
from app.core.config import settings

# Import your existing RAG components
from app.rag.intent_classifier import IntentClassifier, Intent
from app.rag.response_generator import ResponseGenerator


class IntegratedRAGService:
    """
    Production RAG service with database integration
    """
    
    def __init__(self):
        self.faiss_manager = FAISSManager()
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator()
        self.embedding_generator = EmbeddingGenerator()
    
    async def initialize_index(self, db: AsyncSession, document_id: Optional[uuid.UUID] = None):
        """
        Initialize FAISS index from database
        Call this on startup or when documents are added
        """
        await self.faiss_manager.build_index_from_database(db, document_id)
    
    async def ask(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        question: str,
        chapter_id: Optional[uuid.UUID] = None,
        session_id: Optional[uuid.UUID] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Main RAG pipeline for answering questions
        
        Args:
            db: Database session
            user_id: User asking the question
            question: User's question
            chapter_id: Optional chapter context
            session_id: Optional existing chat session
            conversation_history: Optional conversation context
            
        Returns: {
            answer: str,
            intent: str,
            sources: List[Dict],
            session_id: str,
            confidence: float
        }
        """
        start_time = datetime.now()
        
        # Step 1: Classify intent
        intent = self.intent_classifier.classify(question)
        
        # Step 2: Handle based on intent
        if intent in [Intent.GREETING, Intent.FEEDBACK, Intent.OFF_TOPIC]:
            # Direct conversational response (no RAG needed)
            answer = self.response_generator.generate_conversational_response(
                message=question,
                history=conversation_history
            )
            sources = []
            
        elif intent == Intent.CLARIFICATION:
            # Handle clarification with minimal context
            answer = self.response_generator.generate_conversational_response(
                message=f"I'd be happy to help clarify. {question}",
                history=conversation_history
            )
            sources = []
            
        else:  # Intent.MATHEMATICAL_QUERY
            # RAG pipeline for study questions
            # Generate query embedding
            query_embedding = self.embedding_generator.generate_embedding(question)
            
            # Search for relevant chunks
            retrieved_chunks = await self.faiss_manager.search_and_retrieve(
                db=db,
                query_embedding=query_embedding,
                k=settings.RETRIEVAL_K
            )
            
            if not retrieved_chunks:
                # No relevant content found
                answer = self.response_generator.generate_conversational_response(
                    message="I don't have enough information to answer that question. Could you rephrase or ask about a different topic?",
                    history=conversation_history
                )
                sources = []
            else:
                # Convert chunks to LangChain Documents
                context_docs = self._chunks_to_documents(retrieved_chunks)
                
                # Generate answer using context
                answer = self.response_generator.generate_rag_response(
                    query=question,
                    context_docs=context_docs
                )
                
                # Format sources
                sources = [
                    {
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"],
                        "score": chunk["score"],
                        "rank": chunk["rank"]
                    }
                    for chunk in retrieved_chunks
                ]
        
        # Step 3: Save conversation to database
        if not session_id:
            # Create new session
            session = await ChatService.create_session(
                db=db,
                user_id=user_id,
                chapter_id=chapter_id
            )
            session_id = session.session_id
        
        # Save user message
        await ChatService.add_message(
            db=db,
            session_id=session_id,
            sender="user",
            content=question
        )
        
        # Save assistant message
        await ChatService.add_message(
            db=db,
            session_id=session_id,
            sender="assistant",
            content=answer
        )
        
        # Calculate response time
        elapsed_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "answer": answer,
            "intent": intent.value,
            "sources": sources,
            "session_id": str(session_id),
            "chunk_count": len(sources),
            "response_time": elapsed_time,
            "timestamp": datetime.now().isoformat()
        }
    
    def _chunks_to_documents(self, chunks: List[Dict[str, Any]]) -> List[Document]:
        """
        Convert retrieved chunks to LangChain Document objects
        """
        documents = []
        for chunk in chunks:
            doc = Document(
                page_content=chunk["content"],
                metadata={
                    "chunk_id": chunk["chunk_id"],
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "score": chunk["score"],
                    "rank": chunk["rank"]
                }
            )
            documents.append(doc)
        return documents
    
    async def get_conversation_history(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for context
        
        Returns: List[{role: 'user'|'assistant', content: str}]
        """
        messages = await ChatService.get_recent_messages(db, session_id, n=limit)
        
        return [
            {
                "role": msg.sender,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current RAG system statistics"""
        return {
            "faiss_index": self.faiss_manager.get_index_stats(),
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.LLM_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "retrieval_k": settings.RETRIEVAL_K
        }
    
    def _build_context(self, chunks: List[Dict[str, Any]], max_length: int = None) -> str:
        """
        Build context string from retrieved chunks
        Respects max_length to avoid token limits
        """
        max_length = max_length or settings.MAX_CONTEXT_LENGTH
        
        context_parts = []
        current_length = 0
        
        for chunk in chunks:
            content = chunk["content"]
            chunk_length = len(content)
            
            if current_length + chunk_length > max_length:
                # Truncate last chunk if needed
                remaining = max_length - current_length
                if remaining > 100:  # Only add if substantial
                    context_parts.append(content[:remaining] + "...")
                break
            
            context_parts.append(content)
            current_length += chunk_length
        
        return "\n\n".join(context_parts)
    
    async def get_conversation_history(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation history for context
        
        Returns: List[{role: 'user'|'assistant', content: str}]
        """
        messages = await ChatService.get_recent_messages(db, session_id, n=limit)
        
        return [
            {
                "role": msg.sender,
                "content": msg.content
            }
            for msg in messages
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current RAG system statistics"""
        return {
            "faiss_index": self.faiss_manager.get_index_stats(),
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm_model": settings.LLM_MODEL,
            "chunk_size": settings.CHUNK_SIZE,
            "retrieval_k": settings.RETRIEVAL_K
        }