"""
Resource Agent Configuration

Manages all configuration settings using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    port: int = Field(default=8003, env="PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    agent_id: str = Field(default="resource-agent-001", env="AGENT_ID")
    agent_type: str = Field(default="resource", env="AGENT_TYPE")
    
    # Orchestrator
    orchestrator_url: str = Field(
        default="http://localhost:8080",
        env="ORCHESTRATOR_URL"
    )
    orchestrator_register_endpoint: str = Field(
        default="/api/v1/agents/register",
        env="ORCHESTRATOR_REGISTER_ENDPOINT"
    )
    orchestrator_heartbeat_interval: int = Field(
        default=30,
        env="ORCHESTRATOR_HEARTBEAT_INTERVAL"
    )
    
    # Database
    database_url: str = Field(
        default="postgresql://resource_user:resource_password@localhost:5432/resource_agent",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/2",
        env="REDIS_URL"
    )
    
    # Prometheus
    prometheus_port: int = Field(default=9093, env="PROMETHEUS_PORT")
    
    # LLM Configuration
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")
    groq_model: str = Field(default="openai/gpt-oss-20b", env="GROQ_MODEL")
    llm_enabled: bool = Field(default=True, env="LLM_ENABLED")
    llm_timeout: int = Field(default=30, env="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, env="LLM_MAX_RETRIES")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
