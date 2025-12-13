from sqlalchemy import Column, String, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base

class Exam(Base):
    __tablename__ = "exams"

    exam_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)    # SEE, CEE
    board = Column(String, nullable=False)   # NEB, etc.
    grade = Column(String, nullable=False)   # "10"
    starting_date = Column(Date, nullable=True)
