"""
Brainly API - Configuration Management

Uses Pydantic Settings for environment variable management.
"""
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # NVIDIA NIM (Primary LLM)
    NVIDIA_NIM_API_KEY: str = ""
    NVIDIA_NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"
    NVIDIA_NIM_MODEL: str = "meta/llama-3.1-70b-instruct"

    # Groq (Fallback LLM)
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Jina AI (Embeddings)
    JINA_AI_API_KEY: str = ""
    JINA_AI_BASE_URL: str = "https://api.jina.ai/v1"
    JINA_AI_MODEL: str = "jina-embeddings-v3"

    # Email (Resend)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@brainly.ai"

    # Slack (Optional)
    SLACK_WEBHOOK_URL: str = ""

    # Sentry
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"

    # Vercel
    VERCEL_URL: str = ""

    # Frontend/Widget URLs
    NEXT_PUBLIC_API_URL: str = ""
    NEXT_PUBLIC_WIDGET_URL: str = ""
    NEXT_PUBLIC_SUPABASE_URL: str = ""
    NEXT_PUBLIC_SUPABASE_ANON_KEY: str = ""

    # Rate Limiting
    RATE_LIMIT_CHAT_PER_MINUTE: int = 30
    RATE_LIMIT_UPLOAD_PER_MINUTE: int = 10

    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    MAX_KB_SIZE_MB: int = 50


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()