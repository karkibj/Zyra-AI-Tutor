"""
Database Handshake File
-----------------------
Async SQLAlchemy setup with NEW models only
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Import Base
from app.models.base import Base

# Import NEW models ONLY (this registers them with Base.metadata)
import app.models.user
import app.models.content
import app.models.curriculum
import app.models.extracted_item
import app.models.exam_spec
import app.models.processing_queue

# OLD models removed - they're renamed to .old files
# import app.models.exam
# import app.models.subject
# import app.models.chapter
# import app.models.document
# import app.models.document_chunk
# import app.models.chunk_embedding
# import app.models.question
# import app.models.attempt
# import app.models.chat_session
# import app.models.chat_message

# -----------------------------
# ASYNC ENGINE
# -----------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.ENV == "development",  # Show SQL in dev mode
    future=True
)

# -----------------------------
# ASYNC SESSION MAKER
# -----------------------------
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# -----------------------------
# DEPENDENCY FOR FASTAPI
# -----------------------------
async def get_db():
    """
    FastAPI dependency to get async database session.
    Automatically closes session after request.
    """
    async with AsyncSessionLocal() as session:
        yield session

# -----------------------------
# DATABASE INITIALIZATION
# -----------------------------
async def init_db():
    """
    Create all tables on startup.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")