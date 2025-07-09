"""
Configuration settings for the Image RAG system.
"""

import os
from typing import Optional, List
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database Configuration
    database_url: str = Field(default="mysql+pymysql://user:password@localhost:3306/image_rag_db")
    
    # Vector Database Configuration (ChromaDB)
    chromadb_host: str = Field(default="localhost")
    chromadb_port: int = Field(default=8000)
    chromadb_collection_name: str = Field(default="image_embeddings")
    
    # Object Storage Configuration (MinIO)
    minio_endpoint: str = Field(default="localhost:9000")
    minio_access_key: str = Field(default="minioadmin")
    minio_secret_key: str = Field(default="minioadmin")
    minio_bucket_name: str = Field(default="image-storage")
    minio_secure: bool = Field(default=False)
    

    
    # ML Model Configuration
    clip_model_name: str = Field(default="ViT-B/32")
    sentence_transformer_model: str = Field(default="all-MiniLM-L6-v2")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)
    api_workers: int = Field(default=4)
    debug: bool = Field(default=True)
    
    # Hybrid Search Configuration
    text_weight: float = Field(default=0.7)
    image_weight: float = Field(default=0.3)
    top_k: int = Field(default=20)
    rerank_top_k: int = Field(default=10)
    

    
    # Upload Configuration
    max_file_size: int = Field(default=10 * 1024 * 1024)  # 10MB
    allowed_extensions: list = Field(default_factory=lambda: ['.jpg', '.jpeg', '.png', '.webp', '.bmp'])
    
    # Embedding Dimensions
    clip_embedding_dim: int = Field(default=512)
    text_embedding_dim: int = Field(default=384)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings 