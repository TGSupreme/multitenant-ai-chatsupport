import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server-level application settings loaded from environment variables or .env file."""

    # Server Application Configuration
    PROJECT_NAME: str = "Stateless Multi-Tenant AI Chat Support Engine"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Server Host & Port
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Qdrant Cloud Vector Database Configuration
    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION_NAME: str = "multitenant_chat_support"

    # Jina Embeddings Configuration
    JINA_EMBEDDINGS_URL: str = "https://api.jina.ai/v1/embeddings"
    JINA_MODEL_NAME: str = "jina-embeddings-v3"

    # LLM Provider Model Listing Base API URLs
    OPENAI_MODELS_API_BASE: str = "https://api.openai.com/v1"
    GROQ_MODELS_API_BASE: str = "https://api.groq.com/openai/v1"
    GEMINI_MODELS_API_BASE: str = "https://generativelanguage.googleapis.com/v1beta"

    # LangSmith Observability & Tracing Configuration
    LANGSMITH_TRACING: bool = False
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_PROJECT: str = "stateless-chat-support"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()

# Export LangSmith variables to environment for LangChain SDK
if settings.LANGSMITH_TRACING:
    # Legacy/Standard LangChain vars
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
    # Modern LangSmith vars
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY or ""
    os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
