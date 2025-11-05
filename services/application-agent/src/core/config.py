"""
Application Agent Configuration

Manages all configuration settings from environment variables.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application Agent settings."""
    
    # Agent Identity
    agent_id: str = "application-agent-001"
    agent_name: str = "Application Agent"
    agent_type: str = "application"
    version: str = "1.0.0"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8004
    environment: str = "development"
    
    # Registration
    registration_enabled: bool = Field(default=True, description="Enable orchestrator registration")
    orchestrator_url: str = Field(default="http://localhost:8000", description="Orchestrator URL")
    heartbeat_interval: int = Field(default=30, description="Heartbeat interval in seconds")
    
    # LLM Configuration
    groq_api_key: Optional[str] = None
    groq_model: str = "openai/gpt-oss-20b"
    llm_enabled: bool = True
    llm_timeout: int = 30
    llm_max_retries: int = 3
    
    # Quality Thresholds
    quality_threshold: float = 0.85  # 85% minimum quality score
    regression_threshold: float = 0.05  # 5% max quality drop
    hallucination_threshold: float = 0.10  # 10% max hallucination rate
    
    # Database Configuration (optional for now)
    database_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
