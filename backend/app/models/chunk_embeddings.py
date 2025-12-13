from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ARRAY
from datetime import datetime
import uuid
from .base import Base

class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    embedding_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("document_chunks.chunk_id"), nullable=False)

    embedding_vector = Column(ARRAY(float))   # or pgvector if installed
    model_name = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
