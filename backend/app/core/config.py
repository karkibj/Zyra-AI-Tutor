from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Zyra API"
    ENV: str = "dev"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Add your Google API key here
    GOOGLE_API_KEY: str

    # Allow loading from .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow"   # <-- Important: Prevents Extra Inputs Error
    )

settings = Settings()
