from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.base import Base


class ExtractedItem(Base):
    """Individual items extracted from content (questions, examples, etc.)"""
    __tablename__ = "extracted_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(
        UUID(as_uuid=True),
        ForeignKey('content.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    item_type = Column(String(50), nullable=False, index=True)
    item_number = Column(String(20), nullable=True)
    text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    chapter = Column(String(50), nullable=True, index=True)
    topic = Column(String(100), nullable=True)
    cognitive_level = Column(String(10), nullable=True, index=True)
    difficulty = Column(String(20), nullable=True, index=True)
    marks = Column(Integer, nullable=True)
    embedding_id = Column(String(100), nullable=True)

    item_metadata = Column("metadata", JSON, nullable=True)  # ✅ FIXED

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content = relationship("Content", back_populates="extracted_items")
    
    __table_args__ = (
        Index('idx_item_classification', 'item_type', 'cognitive_level', 'difficulty'),
        Index('idx_item_chapter', 'chapter', 'marks'),
    )
