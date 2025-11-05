"""
Metrics Collection Endpoints

API endpoints for collecting metrics from LLM inference engines.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
import logging

from src.models.metrics import (
    VLLMMetricsSnapshot,
    TGIMetricsSnapshot,
    SGLangMetricsSnapshot,
    MetricsCollectionRequest,
    MetricsCollectionResponse
)
from src.collectors.vllm_collector import VLLMCollector
from src.collectors.tgi_collector import TGICollector
from src.collectors.sglang_collector import SGLangCollector

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/collect/vllm",
    response_model=MetricsCollectionResponse,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def collect_vllm_metrics(
    request: MetricsCollectionRequest
) -> MetricsCollectionResponse:
    """
    Collect metrics from a vLLM instance.
    
    Args:
        request: Collection request with instance details
        
    Returns:
        Collection response with metrics or error
    """
    try:
        async with VLLMCollector(timeout=request.timeout) as collector:
            metrics = await collector.collect(
                instance_id=request.instance_id,
                endpoint=request.endpoint
            )
        
        return MetricsCollectionResponse(
            success=True,
            instance_id=request.instance_id,
            metrics=metrics
        )
    
    except Exception as e:
        logger.error(
            f"Failed to collect metrics from {request.instance_id}: {e}",
            exc_info=True
        )
        
        return MetricsCollectionResponse(
            success=False,
            instance_id=request.instance_id,
            error=str(e)
        )


@router.get(
    "/metrics/vllm/{instance_id}",
    response_model=VLLMMetricsSnapshot,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def get_vllm_metrics(
    instance_id: str,
    endpoint: str
) -> VLLMMetricsSnapshot:
    """
    Get current metrics from a vLLM instance.
    
    Args:
        instance_id: vLLM instance identifier
        endpoint: Prometheus metrics endpoint URL
        
    Returns:
        Current metrics snapshot
        
    Raises:
        HTTPException: If collection fails
    """
    try:
        async with VLLMCollector() as collector:
            metrics = await collector.collect(
                instance_id=instance_id,
                endpoint=endpoint
            )
        
        return metrics
    
    except Exception as e:
        logger.error(
            f"Failed to get metrics from {instance_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect metrics: {str(e)}"
        )


@router.post(
    "/collect/tgi",
    response_model=MetricsCollectionResponse,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def collect_tgi_metrics(
    request: MetricsCollectionRequest
) -> MetricsCollectionResponse:
    """
    Collect metrics from a TGI instance.
    
    Args:
        request: Collection request with instance details
        
    Returns:
        Collection response with metrics or error
    """
    try:
        async with TGICollector(timeout=request.timeout) as collector:
            metrics = await collector.collect(
                instance_id=request.instance_id,
                endpoint=request.endpoint
            )
        
        return MetricsCollectionResponse(
            success=True,
            instance_id=request.instance_id,
            metrics=metrics
        )
    
    except Exception as e:
        logger.error(
            f"Failed to collect TGI metrics from {request.instance_id}: {e}",
            exc_info=True
        )
        
        return MetricsCollectionResponse(
            success=False,
            instance_id=request.instance_id,
            error=str(e)
        )


@router.get(
    "/metrics/tgi/{instance_id}",
    response_model=TGIMetricsSnapshot,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def get_tgi_metrics(
    instance_id: str,
    endpoint: str
) -> TGIMetricsSnapshot:
    """
    Get current metrics from a TGI instance.
    
    Args:
        instance_id: TGI instance identifier
        endpoint: Prometheus metrics endpoint URL
        
    Returns:
        Current metrics snapshot
        
    Raises:
        HTTPException: If collection fails
    """
    try:
        async with TGICollector() as collector:
            metrics = await collector.collect(
                instance_id=instance_id,
                endpoint=endpoint
            )
        
        return metrics
    
    except Exception as e:
        logger.error(
            f"Failed to get TGI metrics from {instance_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect TGI metrics: {str(e)}"
        )


@router.post(
    "/collect/sglang",
    response_model=MetricsCollectionResponse,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def collect_sglang_metrics(
    request: MetricsCollectionRequest
) -> MetricsCollectionResponse:
    """
    Collect metrics from a SGLang instance.
    
    Args:
        request: Collection request with instance details
        
    Returns:
        Collection response with metrics or error
    """
    try:
        async with SGLangCollector(timeout=request.timeout) as collector:
            metrics = await collector.collect(
                instance_id=request.instance_id,
                endpoint=request.endpoint
            )
        
        return MetricsCollectionResponse(
            success=True,
            instance_id=request.instance_id,
            metrics=metrics
        )
    
    except Exception as e:
        logger.error(
            f"Failed to collect SGLang metrics from {request.instance_id}: {e}",
            exc_info=True
        )
        
        return MetricsCollectionResponse(
            success=False,
            instance_id=request.instance_id,
            error=str(e)
        )


@router.get(
    "/metrics/sglang/{instance_id}",
    response_model=SGLangMetricsSnapshot,
    status_code=status.HTTP_200_OK,
    tags=["metrics"]
)
async def get_sglang_metrics(
    instance_id: str,
    endpoint: str
) -> SGLangMetricsSnapshot:
    """
    Get current metrics from a SGLang instance.
    
    Args:
        instance_id: SGLang instance identifier
        endpoint: Prometheus metrics endpoint URL
        
    Returns:
        Current metrics snapshot
        
    Raises:
        HTTPException: If collection fails
    """
    try:
        async with SGLangCollector() as collector:
            metrics = await collector.collect(
                instance_id=instance_id,
                endpoint=endpoint
            )
        
        return metrics
    
    except Exception as e:
        logger.error(
            f"Failed to get SGLang metrics from {instance_id}: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect SGLang metrics: {str(e)}"
        )


@router.get(
    "/history/{instance_id}",
    response_model=List[Dict[str, Any]],
    tags=["metrics"]
)
async def get_metrics_history(
    instance_id: str,
    hours: int = 24,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get metrics history for an instance.
    
    Args:
        instance_id: Instance identifier
        hours: Number of hours of history (default 24)
        limit: Maximum number of data points (default 100)
        
    Returns:
        List of historical metrics
    """
    # This would query from a time-series database in production
    # For now, return empty list
    logger.info(f"Fetching {hours}h of metrics history for {instance_id}")
    return []
