"""Configuration settings"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Get project root directory (2 levels up from this file)
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings"""
    
    database_url: str = "postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra"
    clickhouse_url: str = "http://localhost:8123"
    redis_url: str = "redis://localhost:6379"
    qdrant_url: str = "http://localhost:6333"
    
    class Config:
        env_file = str(ENV_FILE)
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # Ignore extra fields in .env file


settings = Settings()
