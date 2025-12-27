from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class Subject(Base):
    """Subject model for academic subjects"""
    __tablename__ = "subjects"

    subject_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.exam_id"), nullable=False)
    name = Column(String, nullable=False)
    code = Column(String, nullable=True)
    description = Column(String, nullable=True)
    full_mark = Column(Integer, nullable=True)
    pass_mark = Column(Integer, nullable=True)
    theory_mark = Column(Integer, nullable=True)
    practical_mark = Column(Integer, nullable=True)

    # Relationships
    exam = relationship("Exam", back_populates="subjects")
    chapters = relationship("Chapter", back_populates="subject")
    documents = relationship("Document", back_populates="subject")
    questions = relationship("Question", back_populates="subject")

    def __repr__(self):
        return f"<Subject(subject_id={self.subject_id}, name={self.name}, code={self.code})>"