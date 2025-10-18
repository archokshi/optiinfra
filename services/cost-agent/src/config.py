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

    # LangGraph Configuration
    enable_graph_visualization: bool = True
    max_workflow_iterations: int = 10
    workflow_timeout_seconds: int = 300

    # LLM Configuration (for future use)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    default_llm_provider: str = "mock"  # "openai", "anthropic", or "mock"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
