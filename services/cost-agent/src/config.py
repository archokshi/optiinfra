"""
Configuration management for Cost Agent.
Loads settings from environment variables.
"""

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    app_name: str = "OptiInfra Cost Agent"
    environment: str = "development"
    port: int = 8001
    log_level: str = "INFO"

    # Orchestrator
    orchestrator_url: Optional[str] = "http://localhost:8080"
    agent_id: str = "cost-agent-001"
    agent_type: str = "cost"

    # Database (for later use)
    database_url: Optional[str] = None

    # Redis (for later use)
    redis_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
