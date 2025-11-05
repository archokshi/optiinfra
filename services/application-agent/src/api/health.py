"""
Health Check Endpoints

Provides health status and readiness checks for the Application Agent.
"""

from fastapi import APIRouter, status
from typing import Dict, Any
from datetime import datetime
from ..core.config import settings
from ..core.registration import orchestrator_client

router = APIRouter(tags=["health"])


@router.get("/", status_code=status.HTTP_200_OK)
async def root() -> Dict[str, Any]:
    """Root endpoint."""
    return {
        "agent": settings.agent_name,
        "version": settings.version,
        "status": "active",
        "agent_id": settings.agent_id
    }


@router.get("/health/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": settings.agent_id
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health() -> Dict[str, Any]:
    """Detailed health check with component status."""
    components = {
        "orchestrator": "healthy" if orchestrator_client.registered else "disconnected",
        "api": "healthy"
    }
    
    overall_status = "healthy" if all(
        s == "healthy" for s in components.values()
    ) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "agent_id": settings.agent_id,
        "version": settings.version,
        "components": components,
        "uptime_seconds": 0  # TODO: Track actual uptime
    }


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, str]:
    """Kubernetes readiness probe."""
    return {"status": "ready"}


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Kubernetes liveness probe."""
    return {"status": "alive"}
