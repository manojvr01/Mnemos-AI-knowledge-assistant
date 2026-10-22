from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Mnemos API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mnemos_user:mnemos_password@localhost:5432/mnemos_dev"
    
    # Security
    JWT_SECRET: str = "dev_jwt_secret_change_in_production_min32chars"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    COOKIE_SECURE: bool = False

    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_ROOT: str = "./data/storage"

    # AI & Embeddings (Google Gemini API)
    EMBEDDING_PROVIDER: str = "gemini"  # "gemini" or "mock"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSION: int = 768
    LLM_PROVIDER: str = "gemini"  # "gemini" or "mock"
    GEMINI_CHAT_MODEL: str = "gemini-3.5-flash"
    GEMINI_API_KEY: str = ""

    # Legacy / fallback aliases
    @property
    def EMBEDDING_MODEL(self) -> str:
        return self.GEMINI_EMBEDDING_MODEL

    @property
    def LLM_MODEL(self) -> str:
        return self.GEMINI_CHAT_MODEL

    # RAG
    RAG_SIMILARITY_THRESHOLD: float = 0.50
    RAG_TOP_K: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
