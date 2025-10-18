"""
Health check endpoint for Cost Agent.
"""

import time

from fastapi import APIRouter

from src.config import settings
from src.models.health import HealthResponse

router = APIRouter()

# Track startup time
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns:
        HealthResponse: Current health status with uptime
    """
    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy",
        version="0.1.0",
        agent_id=settings.agent_id,
        agent_type=settings.agent_type,
        uptime_seconds=uptime,
    )
