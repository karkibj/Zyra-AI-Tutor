"""
User Model - Authentication & Authorization
Compatible with existing database structure
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base  # CHANGED THIS LINE!


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    # Primary Key (UUID string format for compatibility)
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Authentication
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Null for Google OAuth users
    
    # Profile
    full_name = Column(String(100), nullable=True)
    picture = Column(String, nullable=True)  # Avatar URL (Google)
    
    # Authorization
    role = Column(String(20), default="student", nullable=False)  # 'admin', 'teacher', 'student'
    
    # Provider tracking
    provider = Column(String(50), default="local")  # 'local' or 'google'
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())