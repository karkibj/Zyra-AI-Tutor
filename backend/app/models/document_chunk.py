from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, func
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class DocumentChunk(Base):
    """Document chunk model for storing processed text segments"""
    __tablename__ = "document_chunks"

    chunk_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    chunk_type = Column(String(50), nullable=True)  # 'text', 'formula', 'table'
    meta_data = Column(JSON, nullable=True)  # Changed from 'metadata' (reserved word)
    start_index = Column(Integer, nullable=True)
    end_index = Column(Integer, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    document = relationship("Document", back_populates="chunks")
    embedding = relationship("ChunkEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DocumentChunk(chunk_id={self.chunk_id}, document_id={self.document_id}, chunk_index={self.chunk_index})>"