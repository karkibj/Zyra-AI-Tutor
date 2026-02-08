from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey, Index, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.models.base import Base


class ExamSpecification(Base):
    """Exam specifications and patterns - Separate from curriculum"""
    __tablename__ = "exam_specifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_node_id = Column(UUID(as_uuid=True), ForeignKey('curriculum_nodes.id', ondelete='CASCADE'), nullable=False, index=True)
    spec_type = Column(String(50), nullable=False, index=True)
    value = Column(JSON, nullable=False)
    year = Column(Integer, nullable=False, index=True)
    version = Column(String(50), default='1.0')
    active = Column(Boolean, default=True, index=True)
    notes = Column(Text, nullable=True)
    source = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    curriculum_node = relationship("CurriculumNode", back_populates="exam_specs")
    
    __table_args__ = (
        Index('idx_spec_active_year', 'active', 'year', 'spec_type'),
        Index('idx_spec_curriculum', 'curriculum_node_id', 'active'),
    )