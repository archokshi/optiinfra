"""
Health Check Endpoints

Provides health check and service information endpoints.
"""

from fastapi import APIRouter, status
from datetime import datetime
import time

from src.models.health import (
    HealthResponse,
    DetailedHealthResponse,
    ServiceInfo
)
from src.config import settings

router = APIRouter()

# Track startup time
_startup_time = time.time()


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.
    
    Returns:
        HealthResponse: Current health status
    """
    return HealthResponse(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=time.time() - _startup_time
    )


@router.get(
    "/health/detailed",
    response_model=DetailedHealthResponse,
    status_code=status.HTTP_200_OK,
    tags=["health"]
)
async def detailed_health_check() -> DetailedHealthResponse:
    """
    Detailed health check with component status.
    
    Returns:
        DetailedHealthResponse: Detailed health status
    """
    # TODO: Add actual component health checks
    components = {
        "database": {"status": "healthy", "latency_ms": 5.2},
        "cache": {"status": "healthy", "latency_ms": 1.1},
        "orchestrator": {"status": "healthy", "latency_ms": 10.5}
    }
    
    return DetailedHealthResponse(
        status="healthy",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=time.time() - _startup_time,
        components=components
    )


@router.get(
    "/",
    response_model=ServiceInfo,
    status_code=status.HTTP_200_OK,
    tags=["info"]
)
async def service_info() -> ServiceInfo:
    """
    Service information endpoint.
    
    Returns:
        ServiceInfo: Service details and capabilities
    """
    return ServiceInfo()
