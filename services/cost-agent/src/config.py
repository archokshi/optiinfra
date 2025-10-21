"""Configuration management for Cost Agent.
Loads settings from environment variables.
"""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Service
    SERVICE_NAME: str = "cost-agent"
    SERVICE_PORT: int = 8001
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://optiinfra:password@localhost:5432/optiinfra"
    CLICKHOUSE_URL: str = "http://localhost:8123"
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Orchestrator
    ORCHESTRATOR_URL: str = "http://localhost:8080"
    
    # LLM (will be used in 1.8)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Cloud Providers (will be used in 1.2-1.4)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    
    GCP_PROJECT_ID: Optional[str] = None
    GCP_CREDENTIALS_PATH: Optional[str] = None
    
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    
    # Analysis
    ANALYSIS_LOOKBACK_DAYS: int = 30
    SPOT_SAVINGS_TARGET: float = 0.35  # 35% target
    RI_SAVINGS_TARGET: float = 0.50    # 50% target
    
    # LangGraph Configuration
    enable_graph_visualization: bool = True
    max_workflow_iterations: int = 10
    workflow_timeout_seconds: int = 300
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
