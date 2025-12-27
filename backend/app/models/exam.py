from sqlalchemy import Column, String, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class Exam(Base):
    """Exam model for examinations (e.g., SEE, NEB)"""
    __tablename__ = "exams"

    exam_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    board = Column(String, nullable=False)  # e.g., NEB, CTEVT
    grade = Column(String, nullable=False)  # e.g., Grade 10, Grade 12
    starting_date = Column(Date, nullable=True)

    # Relationships
    subjects = relationship("Subject", back_populates="exam")

    def __repr__(self):
        return f"<Exam(exam_id={self.exam_id}, name={self.name}, board={self.board}, grade={self.grade})>"