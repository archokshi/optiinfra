"""Configuration management for Cost Agent.
Loads settings from environment variables.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Service
    SERVICE_NAME: str = "cost-agent"
    SERVICE_PORT: int = 8001
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "postgresql://optiinfra:optiinfra_dev_password@localhost:5432/optiinfra"
    CLICKHOUSE_URL: str = "http://localhost:8123"
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_DATABASE: str = "optiinfra_metrics"
    QDRANT_URL: str = "http://localhost:6333"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Orchestrator
    ORCHESTRATOR_URL: str = "http://localhost:8080"
    
    # LLM Configuration (PHASE1-1.8)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    LLM_ENABLED: bool = True
    LLM_CACHE_TTL: int = 3600  # 1 hour
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT: int = 30  # seconds
    LLM_MAX_TOKENS: int = 2000
    LLM_TEMPERATURE: float = 0.7
    
    # Legacy LLM keys (for future use)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Cloud Providers (will be used in 1.2-1.4)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_REGIONS: list = ["us-east-1", "us-west-2", "eu-west-1"]
    
    # AWS Cost Collection Settings
    AWS_COST_LOOKBACK_DAYS: int = 30
    AWS_IDLE_CPU_THRESHOLD: float = 5.0  # CPU < 5% = idle
    AWS_UNDERUTILIZED_CPU_THRESHOLD: float = 20.0  # CPU < 20% = underutilized
    AWS_SPOT_SAVINGS_TARGET: float = 0.35  # 35% target savings
    AWS_COLLECTION_SCHEDULE: str = "0 2 * * *"  # Daily at 2 AM
    
    GCP_PROJECT_ID: Optional[str] = None
    GCP_CREDENTIALS_PATH: Optional[str] = None
    GCP_BILLING_ACCOUNT_ID: Optional[str] = None
    GCP_BILLING_DATASET: str = "billing_export"
    
    # GCP Cost Collection Settings
    GCP_COST_LOOKBACK_DAYS: int = 30
    GCP_IDLE_CPU_THRESHOLD: float = 5.0  # CPU < 5% = idle
    GCP_UNDERUTILIZED_CPU_THRESHOLD: float = 20.0  # CPU < 20% = underutilized
    GCP_PREEMPTIBLE_SAVINGS_TARGET: float = 0.80  # 80% target savings
    GCP_COLLECTION_SCHEDULE: str = "0 3 * * *"  # Daily at 3 AM
    
    AZURE_SUBSCRIPTION_ID: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None
    AZURE_CLIENT_SECRET: Optional[str] = None
    
    # Azure Cost Collection Settings
    AZURE_COST_LOOKBACK_DAYS: int = 30
    AZURE_IDLE_CPU_THRESHOLD: float = 5.0  # CPU < 5% = idle
    AZURE_UNDERUTILIZED_CPU_THRESHOLD: float = 20.0  # CPU < 20% = underutilized
    AZURE_SPOT_SAVINGS_TARGET: float = 0.70  # 70% target savings (Azure Spot)
    AZURE_COLLECTION_SCHEDULE: str = "0 4 * * *"  # Daily at 4 AM
    AZURE_DEFAULT_LOCATION: str = "eastus"
    AZURE_LOCATIONS: list = ["eastus", "westus2", "westeurope"]
    
    # Analysis
    ANALYSIS_LOOKBACK_DAYS: int = 30
    SPOT_SAVINGS_TARGET: float = 0.35  # 35% target
    RI_SAVINGS_TARGET: float = 0.50    # 50% target
    
    # LangGraph Configuration
    enable_graph_visualization: bool = True
    max_workflow_iterations: int = 10
    workflow_timeout_seconds: int = 300
    
# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
