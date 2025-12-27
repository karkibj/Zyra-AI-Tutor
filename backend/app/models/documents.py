from sqlalchemy import Column, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class Document(Base):
    """Document model for storing uploaded educational materials"""
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.chapter_id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    source_link = Column(String, nullable=True)
    language = Column(String, nullable=True)
    type = Column(String, nullable=True)  # pdf, docx, etc.
    status = Column(String, nullable=True)  # pending, processing, completed, failed
    
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=False), onupdate=func.now())

    # Relationships
    chapter = relationship("Chapter", back_populates="documents")
    subject = relationship("Subject", back_populates="documents")
    uploader = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(document_id={self.document_id}, title={self.title}, status={self.status})>"