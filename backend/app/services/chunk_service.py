"""
Chunk Service - Async CRUD operations for document chunks
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
import uuid

from app.models.document_chunk import DocumentChunk


class ChunkService:
    """Service for managing document chunks"""

    @staticmethod
    async def create_chunk(
        db: AsyncSession,
        document_id: uuid.UUID,
        chunk_index: int,
        content: str,
        token_count: int,
        chunk_type: str = "text",
        meta_data: Optional[Dict[str, Any]] = None,
        start_index: Optional[int] = None,
        end_index: Optional[int] = None
    ) -> DocumentChunk:
        """Create a single chunk"""
        chunk = DocumentChunk(
            chunk_id=uuid.uuid4(),
            document_id=document_id,
            chunk_index=chunk_index,
            content=content,
            token_count=token_count,
            chunk_type=chunk_type,
            meta_data=meta_data,
            start_index=start_index,
            end_index=end_index
        )
        
        db.add(chunk)
        await db.commit()
        await db.refresh(chunk)
        return chunk

    @staticmethod
    async def create_chunks_batch(
        db: AsyncSession,
        chunks_data: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Create multiple chunks in a batch (more efficient)"""
        chunks = []
        for chunk_data in chunks_data:
            chunk = DocumentChunk(
                chunk_id=uuid.uuid4(),
                document_id=chunk_data["document_id"],
                chunk_index=chunk_data["chunk_index"],
                content=chunk_data["content"],
                token_count=chunk_data["token_count"],
                chunk_type=chunk_data.get("chunk_type", "text"),
                meta_data=chunk_data.get("meta_data"),
                start_index=chunk_data.get("start_index"),
                end_index=chunk_data.get("end_index")
            )
            chunks.append(chunk)
        
        db.add_all(chunks)
        await db.commit()
        
        # Refresh all chunks
        for chunk in chunks:
            await db.refresh(chunk)
        
        return chunks

    @staticmethod
    async def get_chunk(db: AsyncSession, chunk_id: uuid.UUID) -> Optional[DocumentChunk]:
        """Get a chunk by ID"""
        stmt = select(DocumentChunk).where(DocumentChunk.chunk_id == chunk_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_chunk_with_embedding(db: AsyncSession, chunk_id: uuid.UUID) -> Optional[DocumentChunk]:
        """Get a chunk with its embedding loaded"""
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.embedding))
            .where(DocumentChunk.chunk_id == chunk_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_chunks_by_document(
        db: AsyncSession,
        document_id: uuid.UUID,
        load_embeddings: bool = False
    ) -> List[DocumentChunk]:
        """Get all chunks for a document, ordered by chunk_index"""
        stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id)
        
        if load_embeddings:
            stmt = stmt.options(selectinload(DocumentChunk.embedding))
        
        stmt = stmt.order_by(DocumentChunk.chunk_index)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_chunks_by_type(
        db: AsyncSession,
        document_id: uuid.UUID,
        chunk_type: str
    ) -> List[DocumentChunk]:
        """Get chunks of a specific type (text/formula/table)"""
        stmt = (
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id == document_id,
                DocumentChunk.chunk_type == chunk_type
            )
            .order_by(DocumentChunk.chunk_index)
        )
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_chunks_without_embeddings(
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> List[DocumentChunk]:
        """Get chunks that don't have embeddings yet"""
        from app.models.chunk_embeddings import ChunkEmbedding
        
        # Subquery to find chunk_ids that have embeddings
        subquery = select(ChunkEmbedding.chunk_id)
        
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.chunk_id.not_in(subquery))
        )
        
        if document_id:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        
        stmt = stmt.limit(limit)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_chunks_by_document(db: AsyncSession, document_id: uuid.UUID) -> int:
        """Delete all chunks for a document (cascades to embeddings)"""
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount

    @staticmethod
    async def count_chunks(
        db: AsyncSession,
        document_id: Optional[uuid.UUID] = None,
        chunk_type: Optional[str] = None
    ) -> int:
        """Count chunks with optional filters"""
        stmt = select(func.count(DocumentChunk.chunk_id))
        
        if document_id:
            stmt = stmt.where(DocumentChunk.document_id == document_id)
        if chunk_type:
            stmt = stmt.where(DocumentChunk.chunk_type == chunk_type)
        
        result = await db.execute(stmt)
        return result.scalar_one()