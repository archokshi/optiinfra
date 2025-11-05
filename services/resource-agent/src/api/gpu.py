"""
GPU Metrics API

Endpoints for GPU metrics collection and retrieval.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Optional

from src.models.gpu_metrics import GPUMetricsCollection
from src.collectors.gpu_collector import GPUCollector
from src.config import settings

router = APIRouter(prefix="/gpu", tags=["gpu"])


@router.get(
    "/metrics",
    response_model=GPUMetricsCollection,
    status_code=status.HTTP_200_OK,
    summary="Get current GPU metrics"
)
async def get_gpu_metrics() -> GPUMetricsCollection:
    """
    Collect and return current GPU metrics from all GPUs.
    
    Returns:
        GPUMetricsCollection: Current GPU metrics
        
    Raises:
        HTTPException: If GPU metrics collection is not available
    """
    with GPUCollector() as collector:
        if not collector.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GPU metrics collection not available (no NVIDIA GPUs or pynvml not installed)"
            )
        
        metrics = collector.collect(instance_id=settings.agent_id)
        
        if metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect GPU metrics"
            )
        
        return metrics


@router.get(
    "/metrics/{gpu_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get metrics for specific GPU"
)
async def get_single_gpu_metrics(gpu_id: int) -> dict:
    """
    Get metrics for a specific GPU.
    
    Args:
        gpu_id: GPU index (0-based)
        
    Returns:
        dict: GPU metrics
        
    Raises:
        HTTPException: If GPU not found or metrics unavailable
    """
    with GPUCollector() as collector:
        if not collector.is_available():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GPU metrics collection not available"
            )
        
        if gpu_id >= collector.gpu_count:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GPU {gpu_id} not found (available: 0-{collector.gpu_count-1})"
            )
        
        gpu_metrics = collector.collect_gpu_metrics(gpu_id)
        
        if gpu_metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to collect metrics for GPU {gpu_id}"
            )
        
        return gpu_metrics.model_dump()


@router.get(
    "/info",
    status_code=status.HTTP_200_OK,
    summary="Get GPU information"
)
async def get_gpu_info() -> dict:
    """
    Get basic GPU information.
    
    Returns:
        dict: GPU count and availability
    """
    with GPUCollector() as collector:
        return {
            "available": collector.is_available(),
            "gpu_count": collector.gpu_count if collector.is_available() else 0,
            "pynvml_installed": collector.initialized
        }
