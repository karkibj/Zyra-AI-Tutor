from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class Subject(Base):
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
