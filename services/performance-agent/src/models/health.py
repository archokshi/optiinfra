"""
Health Check Models

Pydantic models for health check responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class HealthResponse(BaseModel):
    """Basic health check response."""
    
    status: str = Field(..., description="Health status (healthy/unhealthy)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="0.1.0")
    agent_id: str
    agent_type: str
    uptime_seconds: float = Field(..., description="Uptime in seconds")


class DetailedHealthResponse(BaseModel):
    """Detailed health check response with component status."""
    
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(default="0.1.0")
    agent_id: str
    agent_type: str
    uptime_seconds: float
    components: dict = Field(
        default_factory=dict,
        description="Status of individual components"
    )


class ServiceInfo(BaseModel):
    """Service information response."""
    
    service: str = Field(default="OptiInfra Performance Agent")
    version: str = Field(default="0.1.0")
    status: str = Field(default="running")
    capabilities: list[str] = Field(
        default_factory=lambda: [
            "performance_monitoring",
            "bottleneck_detection",
            "kv_cache_optimization",
            "quantization_optimization",
            "batch_size_tuning"
        ]
    )
