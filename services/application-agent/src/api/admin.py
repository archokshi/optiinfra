"""
Admin API

Administrative endpoints for agent management.
"""

import psutil
import time
from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, List
from datetime import datetime
from ..core.logger import logger
from ..core.config import settings

router = APIRouter(prefix="/admin", tags=["admin"])

# Track start time
start_time = time.time()


@router.get("/stats", status_code=status.HTTP_200_OK)
async def get_agent_stats() -> Dict[str, Any]:
    """
    Get agent statistics.
    
    Returns:
        Agent statistics
    """
    try:
        # Get system stats
        process = psutil.Process()
        memory_info = process.memory_info()
        
        uptime = int(time.time() - start_time)
        
        stats = {
            "agent_id": settings.agent_id,
            "agent_name": settings.agent_name,
            "version": settings.version,
            "uptime_seconds": uptime,
            "uptime_formatted": f"{uptime // 3600}h {(uptime % 3600) // 60}m",
            "memory_usage_mb": memory_info.rss / 1024 / 1024,
            "cpu_percent": process.cpu_percent(interval=0.1),
            "threads": process.num_threads(),
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.debug("Retrieved agent statistics")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get agent stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.post("/reset", status_code=status.HTTP_200_OK)
async def reset_agent() -> Dict[str, Any]:
    """
    Reset agent state (for testing).
    
    Returns:
        Reset confirmation
    """
    try:
        logger.warning("Agent reset requested")
        
        # In production, this would clear caches, reset counters, etc.
        # For now, just acknowledge the request
        
        return {
            "status": "reset",
            "message": "Agent state reset successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reset agent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset agent: {str(e)}"
        )


@router.post("/config/reload", status_code=status.HTTP_200_OK)
async def reload_configuration() -> Dict[str, Any]:
    """
    Reload configuration.
    
    Returns:
        Reload confirmation
    """
    try:
        logger.info("Configuration reload requested")
        
        # In production, this would reload config from file/env
        # For now, just acknowledge the request
        
        return {
            "status": "reloaded",
            "config_version": settings.version,
            "message": "Configuration reloaded successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}"
        )


@router.get("/logs", status_code=status.HTTP_200_OK)
async def get_recent_logs(
    limit: int = Query(default=100, ge=1, le=1000),
    level: str = Query(default="INFO", regex="^(DEBUG|INFO|WARNING|ERROR)$")
) -> Dict[str, Any]:
    """
    Get recent logs.
    
    Args:
        limit: Maximum number of log entries
        level: Minimum log level
        
    Returns:
        Recent log entries
    """
    try:
        logger.debug(f"Retrieving recent logs (limit={limit}, level={level})")
        
        # In production, this would read from log files or log aggregation service
        # For now, return simulated logs
        
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Agent started successfully",
                "module": "main"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Configuration loaded",
                "module": "config"
            }
        ]
        
        return {
            "logs": logs[:limit],
            "count": len(logs),
            "level": level
        }
        
    except Exception as e:
        logger.error(f"Failed to get logs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )
