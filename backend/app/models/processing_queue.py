from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.models.base import Base

class ProcessingQueue(Base):
    """
    Queue for background processing tasks
    
    When admin uploads a file, it goes through several processing steps:
    1. Text extraction (from PDF/DOCX)
    2. Embedding generation (convert text to vectors)
    3. Item extraction (extract questions, examples)
    4. Thumbnail generation
    5. Quality checks
    
    This table tracks each task's progress
    """
    __tablename__ = "processing_queue"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Links to Content being processed
    content_id = Column(
        UUID(as_uuid=True), 
        ForeignKey('content.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True,
        comment="Which content is being processed"
    )
    
    # Task Type
    task_type = Column(
        String(50), 
        nullable=False, 
        index=True,
        comment="Type: extract_text, generate_embeddings, extract_items, quality_check, thumbnail_generation"
    )
    
    # Processing Status
    status = Column(
        String(50), 
        default='pending', 
        index=True,
        comment="Status: pending, processing, completed, failed"
    )
    
    # Priority (1-10, higher = more urgent)
    priority = Column(
        Integer, 
        default=5,
        comment="Priority for task execution (1=low, 10=urgent)"
    )
    
    # Progress Tracking (0.0 to 100.0)
    progress = Column(
        Float, 
        default=0.0,
        comment="Percentage complete (0.0 to 100.0)"
    )
    
    # Results/Errors
    result = Column(
        JSON, 
        nullable=True,
        comment="Task results stored as JSON (e.g., {'chunks_created': 42, 'embeddings': 42})"
    )
    
    error_message = Column(
        Text, 
        nullable=True,
        comment="Error details if task failed"
    )
    
    # Retry Logic
    attempts = Column(
        Integer, 
        default=0,
        comment="Number of times this task has been attempted"
    )
    
    max_attempts = Column(
        Integer, 
        default=3,
        comment="Maximum retry attempts before giving up"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        index=True,
        comment="When task was queued"
    )
    
    started_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When processing actually started"
    )
    
    completed_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="When task finished (success or failure)"
    )
    
    # Indexes for Performance
    __table_args__ = (
        # Workers query: "Give me pending tasks by priority"
        Index('idx_queue_status_priority', 'status', 'priority', 'created_at'),
    )