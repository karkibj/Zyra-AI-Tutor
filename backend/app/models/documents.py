from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .base import Base

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chapter_id = Column(UUID(as_uuid=True), ForeignKey("chapters.chapter_id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    source_link = Column(String, nullable=True)
    language = Column(String, default="en")
    type = Column(String, default="note")   # note, example, summary
    status = Column(String, default="published")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
