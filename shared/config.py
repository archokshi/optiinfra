"""Configuration settings"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://optiinfra:password@localhost:5432/optiinfra"
    )
    
    clickhouse_url: str = os.getenv(
        "CLICKHOUSE_URL",
        "http://localhost:8123"
    )
    
    redis_url: str = os.getenv(
        "REDIS_URL",
        "redis://localhost:6379"
    )
    
    qdrant_url: str = os.getenv(
        "QDRANT_URL",
        "http://localhost:6333"
    )
    
    class Config:
        env_file = ".env"


settings = Settings()
