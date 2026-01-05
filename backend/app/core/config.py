"""
Application Configuration
Merges best from both repos
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    # -----------------------------
    # PROJECT CONFIG
    # -----------------------------
    PROJECT_NAME: str = "Zyra RAG System"
    ENV: str = "development"  # development / production
    API_PREFIX: str = "/api/v1"
    
    # -----------------------------
    # CORS
    # -----------------------------
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8000"
    ]
    
    # -----------------------------
    # DATABASE
    # -----------------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:bijaya201542@localhost:5432/zyra_rag"
    
    # -----------------------------
    # LLM & EMBEDDINGS
    # -----------------------------
    GOOGLE_API_KEY: str
    
    # LLM Models
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.3
    
    # Embedding Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # -----------------------------
    # RAG CONFIG
    # -----------------------------
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 60
    MIN_CHUNK_SIZE: int = 128
    RETRIEVAL_K: int = 4
    MAX_CONTEXT_LENGTH: int = 3000
    
    # -----------------------------
    # STORAGE
    # -----------------------------
    STORAGE_PATH: str = "storage/documents"
    VECTORSTORE_PATH: str = "storage/vectorstore"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"
    )

    SECRET_KEY: str = "your-secret-key-change-this-in-production" 
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Google OAuth (Optional - leave empty if not using)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()