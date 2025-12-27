"""
Embedding Service - Async CRUD operations for chunk embeddings
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
import uuid
import numpy as np

from app.models.chunk_embeddings import ChunkEmbedding


class EmbeddingService:
    """Service for managing chunk embeddings"""

    @staticmethod
    async def create_embedding(
        db: AsyncSession,
        chunk_id: uuid.UUID,
        embedding_vector: List[float],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> ChunkEmbedding:
        """Create a single embedding"""
        embedding = ChunkEmbedding(
            embedding_id=uuid.uuid4(),
            chunk_id=chunk_id,
            embedding_vector=embedding_vector,
            model_name=model_name
        )
        
        db.add(embedding)
        await db.commit()
        await db.refresh(embedding)
        return embedding

    @staticmethod
    async def create_embeddings_batch(
        db: AsyncSession,
        embeddings_data: List[Dict[str, Any]]
    ) -> List[ChunkEmbedding]:
        """Create multiple embeddings in a batch (more efficient)"""
        embeddings = []
        for emb_data in embeddings_data:
            embedding = ChunkEmbedding(
                embedding_id=uuid.uuid4(),
                chunk_id=emb_data["chunk_id"],
                embedding_vector=emb_data["embedding_vector"],
                model_name=emb_data.get("model_name", "sentence-transformers/all-MiniLM-L6-v2")
            )
            embeddings.append(embedding)
        
        db.add_all(embeddings)
        await db.commit()
        
        # Refresh all embeddings
        for embedding in embeddings:
            await db.refresh(embedding)
        
        return embeddings

    @staticmethod
    async def get_embedding(db: AsyncSession, embedding_id: uuid.UUID) -> Optional[ChunkEmbedding]:
        """Get an embedding by ID"""
        stmt = select(ChunkEmbedding).where(ChunkEmbedding.embedding_id == embedding_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_embedding_by_chunk(db: AsyncSession, chunk_id: uuid.UUID) -> Optional[ChunkEmbedding]:
        """Get embedding for a specific chunk"""
        stmt = select(ChunkEmbedding).where(ChunkEmbedding.chunk_id == chunk_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_embedding_with_chunk(db: AsyncSession, chunk_id: uuid.UUID) -> Optional[ChunkEmbedding]:
        """Get embedding with its chunk loaded"""
        stmt = (
            select(ChunkEmbedding)
            .options(selectinload(ChunkEmbedding.chunk))
            .where(ChunkEmbedding.chunk_id == chunk_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_embeddings_by_document(
        db: AsyncSession,
        document_id: uuid.UUID
    ) -> List[ChunkEmbedding]:
        """Get all embeddings for a document's chunks"""
        from app.models.document_chunk import DocumentChunk
        
        stmt = (
            select(ChunkEmbedding)
            .join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.chunk_id)
            .where(DocumentChunk.document_id == document_id)
            .options(selectinload(ChunkEmbedding.chunk))
            .order_by(DocumentChunk.chunk_index)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_all_embeddings_for_search(
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None,
        limit: Optional[int] = None
    ) -> List[ChunkEmbedding]:
        """
        Get all embeddings for similarity search
        Used to build FAISS index or perform search
        """
        from app.models.document_chunk import DocumentChunk
        
        stmt = (
            select(ChunkEmbedding)
            .join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.chunk_id)
            .options(selectinload(ChunkEmbedding.chunk))
        )
        
        if document_id:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_embedding(db: AsyncSession, embedding_id: uuid.UUID) -> bool:
        """Delete an embedding"""
        stmt = delete(ChunkEmbedding).where(ChunkEmbedding.embedding_id == embedding_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def delete_embeddings_by_chunk(db: AsyncSession, chunk_id: uuid.UUID) -> bool:
        """Delete embedding for a specific chunk"""
        stmt = delete(ChunkEmbedding).where(ChunkEmbedding.chunk_id == chunk_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def count_embeddings(
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None
    ) -> int:
        """Count embeddings with optional document filter"""
        if document_id:
            from app.models.document_chunk import DocumentChunk
            
            stmt = (
                select(func.count(ChunkEmbedding.embedding_id))
                .join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.chunk_id)
                .where(DocumentChunk.document_id == document_id)
            )
        else:
            stmt = select(func.count(ChunkEmbedding.embedding_id))
        
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    def calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors (utility function)"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))