"""
Health Check Models

Pydantic models for health check endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime


class HealthStatus(BaseModel):
    """Health status response."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    version: str = Field(default="1.0.0", description="Agent version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-24T12:00:00Z",
                "agent_id": "resource-agent-001",
                "agent_type": "resource",
                "version": "1.0.0",
                "uptime_seconds": 3600.0
            }
        }


class DetailedHealthStatus(HealthStatus):
    """Detailed health status with component checks."""
    
    components: Dict[str, str] = Field(
        default_factory=dict,
        description="Component health status"
    )
    metrics: Optional[Dict[str, float]] = Field(
        default=None,
        description="Health metrics"
    )
