"""
Health check response models.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model"""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="Application version")
    agent_id: str = Field(..., description="Agent identifier")
    agent_type: str = Field(..., description="Agent type")
    uptime_seconds: float = Field(..., description="Uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-10-17T10:00:00Z",
                "version": "0.1.0",
                "agent_id": "cost-agent-001",
                "agent_type": "cost",
                "uptime_seconds": 120.5,
            }
        }


class AgentRegistration(BaseModel):
    """Agent registration model for orchestrator"""

    agent_id: str = Field(..., description="Unique agent identifier")
    agent_type: str = Field(..., description="Type of agent")
    host: str = Field(..., description="Agent host")
    port: int = Field(..., description="Agent port")
    capabilities: list[str] = Field(..., description="Agent capabilities")

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "cost-agent-001",
                "agent_type": "cost",
                "host": "localhost",
                "port": 8001,
                "capabilities": [
                    "spot_migration",
                    "reserved_instances",
                    "right_sizing",
                ],
            }
        }
