"""
Health Check Endpoints

Provides health check and readiness endpoints for the Resource Agent.
"""

from fastapi import APIRouter, status
from src.models.health import HealthStatus, DetailedHealthStatus
from src.config import settings
from datetime import datetime
import time

router = APIRouter(prefix="/health", tags=["health"])

# Track startup time
startup_time = time.time()


@router.get(
    "/",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Basic health check"
)
async def health_check() -> HealthStatus:
    """
    Basic health check endpoint.
    
    Returns:
        HealthStatus: Current health status
    """
    uptime = time.time() - startup_time
    
    return HealthStatus(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=uptime
    )


@router.get(
    "/detailed",
    response_model=DetailedHealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Detailed health check"
)
async def detailed_health_check() -> DetailedHealthStatus:
    """
    Detailed health check with component status.
    
    Returns:
        DetailedHealthStatus: Detailed health information
    """
    uptime = time.time() - startup_time
    
    # Check components (placeholder - will be implemented later)
    components = {
        "database": "healthy",
        "redis": "healthy",
        "nvidia_smi": "healthy",
        "orchestrator": "healthy"
    }
    
    metrics = {
        "uptime_seconds": uptime,
        "memory_usage_mb": 0.0,  # Placeholder
        "cpu_usage_percent": 0.0  # Placeholder
    }
    
    return DetailedHealthStatus(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=uptime,
        components=components,
        metrics=metrics
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check"
)
async def readiness_check() -> dict:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        dict: Readiness status
    """
    return {"ready": True}


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check"
)
async def liveness_check() -> dict:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        dict: Liveness status
    """
    return {"alive": True}
