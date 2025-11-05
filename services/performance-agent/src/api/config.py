"""
Configuration Endpoints

API endpoints for agent configuration.
"""

from fastapi import APIRouter
import logging
from typing import Dict, Any

from src.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/config",
    response_model=Dict[str, Any],
    tags=["config"]
)
def get_config() -> Dict[str, Any]:
    """
    Get agent configuration.
    
    Returns:
        Agent configuration (non-sensitive values only)
    """
    return {
        "agent_id": settings.agent_id,
        "agent_type": settings.agent_type,
        "port": settings.port,
        "log_level": settings.log_level,
        "environment": settings.environment,
        "version": "0.1.0"
    }


@router.get(
    "/capabilities",
    response_model=Dict[str, Any],
    tags=["config"]
)
def get_capabilities() -> Dict[str, Any]:
    """
    Get agent capabilities.
    
    Returns:
        Agent capabilities and supported features
    """
    return {
        "capabilities": [
            "performance_monitoring",
            "bottleneck_detection",
            "slo_monitoring",
            "optimization_recommendations",
            "gradual_rollout",
            "automatic_rollback"
        ],
        "supported_platforms": ["vllm", "tgi", "sglang"],
        "optimization_types": ["kv_cache", "quantization", "batching"],
        "workflow_features": [
            "gradual_rollout",
            "health_monitoring",
            "automatic_rollback",
            "human_approval"
        ]
    }
