"""
Configuration management for SageWrite GraphRAG
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SageWrite GraphRAG"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # Database
    MONGODB_URL: str = Field(
        default="mongodb://localhost:27017/sagewrite",
        env="MONGODB_URL"
    )
    MONGODB_DB_NAME: str = Field(default="sagewrite", env="MONGODB_DB_NAME")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # LLM Provider Selection
    LLM_PROVIDER: str = Field(default="openai", env="LLM_PROVIDER")  # "openai" or "bedrock"
    EMBEDDING_PROVIDER: str = Field(default="openai", env="EMBEDDING_PROVIDER")  # "openai" or "bedrock"
    
    # OpenAI
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    
    # AWS Bedrock
    AWS_ACCESS_KEY_ID: str = Field(default="", env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(default="", env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: str = Field(default="us-east-1", env="AWS_REGION")
    BEDROCK_REGION: str = Field(default="us-east-1", env="BEDROCK_REGION")
    BEDROCK_MODEL_ID: str = Field(
        default="anthropic.claude-sonnet-4-5-20250929-v1:0",
        env="BEDROCK_MODEL_ID"
    )
    BEDROCK_EMBEDDING_MODEL_ID: str = Field(
        default="amazon.titan-embed-text-v2:0",
        env="BEDROCK_EMBEDDING_MODEL_ID"
    )
    
    # Google Gemini (for future migration)
    GOOGLE_GEMINI_API_KEY: str = Field(default="", env="GOOGLE_GEMINI_API_KEY")
    GEMINI_MODEL: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL")
    GEMINI_EMBEDDING_MODEL: str = Field(default="text-embedding-004", env="GEMINI_EMBEDDING_MODEL")
    GEMINI_TEMPERATURE: float = Field(default=0.1, env="GEMINI_TEMPERATURE")
    
    # LangSmith Observability
    LANGCHAIN_TRACING_V2: bool = Field(default=True, env="LANGCHAIN_TRACING_V2")
    LANGCHAIN_API_KEY: str = Field(default="", env="LANGCHAIN_API_KEY")
    LANGCHAIN_PROJECT: str = Field(default="sagewrite-graphrag", env="LANGCHAIN_PROJECT")
    LANGCHAIN_ENDPOINT: str = Field(default="https://api.smith.langchain.com", env="LANGCHAIN_ENDPOINT")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # External API Integration
    EXTERNAL_API_BASE_URL: str = Field(
        default="https://writing-api.sagewrite.com",
        env="EXTERNAL_API_BASE_URL"
    )
    EXTERNAL_API_TOKEN: str = Field(default="", env="EXTERNAL_API_TOKEN")
    EXTERNAL_API_MAX_SECTIONS: int = Field(default=5, env="EXTERNAL_API_MAX_SECTIONS")
    EXTERNAL_API_MIN_TEXT_LENGTH: int = Field(default=50, env="EXTERNAL_API_MIN_TEXT_LENGTH")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
