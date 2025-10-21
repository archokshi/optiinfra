"""
Shared Configuration Management

Centralized configuration with environment variable support.
"""

import os
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    """Database configuration"""
    # PostgreSQL
    postgres_host: str = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port: int = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_db: str = os.getenv('POSTGRES_DB', 'optiinfra')
    postgres_user: str = os.getenv('POSTGRES_USER', 'optiinfra')
    postgres_password: str = os.getenv('POSTGRES_PASSWORD', 'password')
    
    # ClickHouse
    clickhouse_host: str = os.getenv('CLICKHOUSE_HOST', 'localhost')
    clickhouse_port: int = int(os.getenv('CLICKHOUSE_PORT', '8123'))
    clickhouse_db: str = os.getenv('CLICKHOUSE_DB', 'optiinfra')
    clickhouse_user: str = os.getenv('CLICKHOUSE_USER', 'default')
    clickhouse_password: str = os.getenv('CLICKHOUSE_PASSWORD', '')
    
    # Qdrant
    qdrant_host: str = os.getenv('QDRANT_HOST', 'localhost')
    qdrant_port: int = int(os.getenv('QDRANT_PORT', '6333'))
    qdrant_api_key: Optional[str] = os.getenv('QDRANT_API_KEY')
    
    # Redis
    redis_host: str = os.getenv('REDIS_HOST', 'localhost')
    redis_port: int = int(os.getenv('REDIS_PORT', '6379'))
    redis_db: int = int(os.getenv('REDIS_DB', '0'))
    redis_password: Optional[str] = os.getenv('REDIS_PASSWORD')
    
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@dataclass
class OrchestratorConfig:
    """Orchestrator configuration"""
    host: str = os.getenv('ORCHESTRATOR_HOST', 'localhost')
    port: int = int(os.getenv('ORCHESTRATOR_PORT', '8080'))
    
    @property
    def url(self) -> str:
        """Get orchestrator URL"""
        return f"http://{self.host}:{self.port}"


@dataclass
class MockCloudConfig:
    """Mock Cloud Provider configuration"""
    host: str = os.getenv('MOCK_CLOUD_HOST', 'localhost')
    port: int = int(os.getenv('MOCK_CLOUD_PORT', '5000'))
    
    @property
    def url(self) -> str:
        """Get mock cloud URL"""
        return f"http://{self.host}:{self.port}"


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = os.getenv('LOG_LEVEL', 'INFO')
    format: str = os.getenv('LOG_FORMAT', 'json')  # 'json' or 'text'
    output: str = os.getenv('LOG_OUTPUT', 'stdout')  # 'stdout' or file path


@dataclass
class AgentConfig:
    """Agent configuration"""
    name: str = os.getenv('AGENT_NAME', 'agent')
    agent_type: str = os.getenv('AGENT_TYPE', 'generic')
    host: str = os.getenv('AGENT_HOST', 'localhost')
    port: int = int(os.getenv('AGENT_PORT', '8001'))
    version: str = os.getenv('AGENT_VERSION', '1.0.0')
    
    # Heartbeat settings
    heartbeat_interval: int = int(os.getenv('HEARTBEAT_INTERVAL', '30'))  # seconds
    
    # Task settings
    task_timeout: int = int(os.getenv('TASK_TIMEOUT', '300'))  # seconds
    max_concurrent_tasks: int = int(os.getenv('MAX_CONCURRENT_TASKS', '5'))


@dataclass
class Settings:
    """Global settings"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    orchestrator: OrchestratorConfig = field(default_factory=OrchestratorConfig)
    mock_cloud: MockCloudConfig = field(default_factory=MockCloudConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv('ENVIRONMENT', 'development'))
    debug: bool = field(default_factory=lambda: os.getenv('DEBUG', 'false').lower() == 'true')
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == 'production'
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == 'development'


# Global settings instance
settings = Settings()
