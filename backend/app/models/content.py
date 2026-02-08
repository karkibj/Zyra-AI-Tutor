from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.base import Base

class Content(Base):
    """Main content storage - ALL types of educational materials"""
    __tablename__ = "content"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=False, index=True)
    file_path = Column(Text, nullable=False)
    file_type = Column(String(20), nullable=False)
    file_size = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    processing_status = Column(String(50), default='pending', index=True)
    vector_store_id = Column(String(100), nullable=True, index=True)
    chunks_count = Column(Integer, default=0)
    embeddings_created = Column(Boolean, default=False)
    access_type = Column(String(50), default='downloadable')
    preview_url = Column(Text, nullable=True)
    download_url = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)

    content_metadata = Column("metadata", JSON, nullable=True)  # ✅ FIXED

    verified = Column(Boolean, default=False)
    quality_score = Column(Float, nullable=True)
    verification_notes = Column(Text, nullable=True)
    views = Column(Integer, default=0)
    downloads = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    unhelpful_votes = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    curriculum_mappings = relationship(
        "ContentCurriculumMapping",
        back_populates="content",
        cascade="all, delete-orphan"
    )
    extracted_items = relationship(
        "ExtractedItem",
        back_populates="content",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index('idx_content_type_status', 'content_type', 'processing_status'),
    )
