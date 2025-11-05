"""
Security Configuration

Centralized security settings.
"""

from pydantic import BaseSettings
from typing import List


class SecuritySettings(BaseSettings):
    """Security settings."""
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # API Authentication
    API_KEY_ENABLED: bool = True
    API_KEY_HEADER: str = "X-API-Key"
    
    # Request validation
    MAX_REQUEST_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_QUERY_LENGTH: int = 2048
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Security headers
    ENABLE_HSTS: bool = True
    ENABLE_CSP: bool = True
    
    # Session
    SESSION_TIMEOUT: int = 3600  # 1 hour
    
    class Config:
        env_file = ".env"
        env_prefix = "SECURITY_"


# Global security settings
security_settings = SecuritySettings()
