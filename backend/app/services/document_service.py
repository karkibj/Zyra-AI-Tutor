"""
Document Service - Async CRUD operations for documents
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
import uuid

from app.models.documents import Document


class DocumentService:
    """Service for managing documents"""

    @staticmethod
    async def create_document(
        db: AsyncSession,
        chapter_id: uuid.UUID,
        subject_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        title: str,
        description: Optional[str] = None,
        source_link: Optional[str] = None,
        language: str = "en",
        doc_type: str = "pdf",
        status: str = "pending"
    ) -> Document:
        """Create a new document"""
        document = Document(
            document_id=uuid.uuid4(),
            chapter_id=chapter_id,
            subject_id=subject_id,
            uploaded_by=uploaded_by,
            title=title,
            description=description,
            source_link=source_link,
            language=language,
            type=doc_type,
            status=status
        )
        
        db.add(document)
        await db.commit()
        await db.refresh(document)
        return document

    @staticmethod
    async def get_document(db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        """Get a document by ID"""
        stmt = select(Document).where(Document.document_id == document_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_document_with_chunks(db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        """Get a document with all its chunks loaded"""
        stmt = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.document_id == document_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(
        db: AsyncSession,
        chapter_id: Optional[uuid.UUID] = None,
        subject_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Document]:
        """List documents with optional filters"""
        stmt = select(Document)
        
        if chapter_id:
            stmt = stmt.where(Document.chapter_id == chapter_id)
        if subject_id:
            stmt = stmt.where(Document.subject_id == subject_id)
        if status:
            stmt = stmt.where(Document.status == status)
        
        stmt = stmt.limit(limit).offset(offset)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def update_document_status(
        db: AsyncSession,
        document_id: uuid.UUID,
        status: str
    ) -> Optional[Document]:
        """Update document status (pending/processing/completed/failed)"""
        stmt = (
            update(Document)
            .where(Document.document_id == document_id)
            .values(status=status)
            .returning(Document)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_document(db: AsyncSession, document_id: uuid.UUID) -> bool:
        """Delete a document (cascades to chunks and embeddings)"""
        stmt = delete(Document).where(Document.document_id == document_id)
        result = await db.execute(stmt)
        await db.commit()
        return result.rowcount > 0

    @staticmethod
    async def count_documents(
        db: AsyncSession,
        chapter_id: Optional[uuid.UUID] = None,
        subject_id: Optional[uuid.UUID] = None
    ) -> int:
        """Count total documents with optional filters"""
        from sqlalchemy import func
        
        stmt = select(func.count(Document.document_id))
        
        if chapter_id:
            stmt = stmt.where(Document.chapter_id == chapter_id)
        if subject_id:
            stmt = stmt.where(Document.subject_id == subject_id)
        
        result = await db.execute(stmt)
        return result.scalar_one()