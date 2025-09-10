"""
Configuration management for SageWrite GraphRAG
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SageWrite GraphRAG"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    
    # API
    API_V1_STR: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database
    MONGODB_URL: str = Field(
        default="mongodb://admin:password123@localhost:27017/sagewrite?authSource=admin",
        env="MONGODB_URL"
    )
    MONGODB_DATABASE: str = Field(default="sagewrite", env="MONGODB_DATABASE")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # OpenAI
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-3-small", env="OPENAI_EMBEDDING_MODEL")
    
    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    
    # File Upload
    MAX_FILE_SIZE: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    ALLOWED_FILE_TYPES: List[str] = Field(default=["pdf", "txt", "docx"], env="ALLOWED_FILE_TYPES")
    
    # GraphRAG Settings
    MAX_GRAPH_HOPS: int = Field(default=3, env="MAX_GRAPH_HOPS")
    MIN_RELATIONSHIP_STRENGTH: float = Field(default=0.5, env="MIN_RELATIONSHIP_STRENGTH")
    VECTOR_SEARCH_LIMIT: int = Field(default=40, env="VECTOR_SEARCH_LIMIT")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()
