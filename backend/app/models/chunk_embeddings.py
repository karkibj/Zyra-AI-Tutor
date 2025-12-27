from sqlalchemy import Column, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import ARRAY, DOUBLE_PRECISION, TIMESTAMP, UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class ChunkEmbedding(Base):
    """Chunk embedding model for storing vector representations"""
    __tablename__ = "chunk_embeddings"

    embedding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("document_chunks.chunk_id", ondelete="CASCADE"), unique=True, nullable=False)
    
    # Using ARRAY for now, will migrate to pgvector later
    embedding_vector = Column(ARRAY(DOUBLE_PRECISION), nullable=False)
    
    # Future: Use pgvector extension
    # from pgvector.sqlalchemy import Vector
    # embedding_vector = Column(Vector(384), nullable=False)  # 384 for all-MiniLM-L6-v2
    
    model_name = Column(String, default="sentence-transformers/all-MiniLM-L6-v2")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    chunk = relationship("DocumentChunk", back_populates="embedding")

    def __repr__(self):
        return f"<ChunkEmbedding(embedding_id={self.embedding_id}, chunk_id={self.chunk_id}, model={self.model_name})>"