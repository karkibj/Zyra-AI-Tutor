from sqlalchemy import Column, String, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship
from app.models.base import Base
import uuid


class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=False)  # student, teacher, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=False), server_default=func.now())

    # Relationships
    documents = relationship("Document", back_populates="uploader")
    chat_sessions = relationship("ChatSession", back_populates="user")
    attempts = relationship("Attempt", back_populates="user")

    def __repr__(self):
        return f"<User(user_id={self.user_id}, name={self.name}, email={self.email}, role={self.role})>"