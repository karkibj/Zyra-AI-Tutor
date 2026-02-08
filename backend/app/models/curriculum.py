from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.base import Base


class CurriculumNode(Base):
    """Hierarchical curriculum structure - Completely flexible"""
    __tablename__ = "curriculum_nodes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False, index=True)
    node_type = Column(String(50), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('curriculum_nodes.id'), nullable=True, index=True)
    order_num = Column(Integer, nullable=False, default=0)

    node_metadata = Column("metadata", JSON, nullable=True)  # ✅ FIXED

    active = Column(Boolean, default=True, index=True)
    effective_from = Column(DateTime(timezone=True), nullable=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    children = relationship(
        "CurriculumNode",
        backref="parent",
        remote_side=[id]
    )
    content_mappings = relationship(
        "ContentCurriculumMapping",
        back_populates="curriculum_node"
    )
    exam_specs = relationship(
        "ExamSpecification",
        back_populates="curriculum_node"
    )
    
    __table_args__ = (
        Index('idx_curriculum_active_type', 'active', 'node_type'),
        Index('idx_curriculum_parent', 'parent_id', 'order_num'),
    )

class ContentCurriculumMapping(Base):
    """Maps content to curriculum - Many-to-many relationship"""
    __tablename__ = "content_curriculum_mapping"
    
    content_id = Column(UUID(as_uuid=True), ForeignKey('content.id', ondelete='CASCADE'), primary_key=True)
    curriculum_node_id = Column(UUID(as_uuid=True), ForeignKey('curriculum_nodes.id', ondelete='CASCADE'), primary_key=True)
    relevance_score = Column(Float, default=1.0)  # ✅ CORRECT (uppercase Float)
    tags = Column(JSON, nullable=True)
    mapping_type = Column(String(50), default='primary')
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    content = relationship("Content", back_populates="curriculum_mappings")
    curriculum_node = relationship("CurriculumNode", back_populates="content_mappings")
    
    __table_args__ = (
        Index('idx_mapping_curriculum', 'curriculum_node_id', 'relevance_score'),
        Index('idx_mapping_content', 'content_id'),
    )