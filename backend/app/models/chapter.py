from sqlalchemy import Column, String, Boolean, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class Chapter(Base):
    __tablename__ = "chapters"

    chapter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id"), nullable=False)

    name = Column(String, nullable=False)
    chapter_number = Column(Integer, nullable=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
