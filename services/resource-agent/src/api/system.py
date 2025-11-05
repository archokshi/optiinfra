"""
System Metrics API

Endpoints for system metrics collection and retrieval.
"""

from fastapi import APIRouter, HTTPException, status

from src.models.system_metrics import SystemMetricsCollection
from src.collectors.system_collector import SystemCollector
from src.config import settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get(
    "/metrics",
    response_model=SystemMetricsCollection,
    status_code=status.HTTP_200_OK,
    summary="Get current system metrics"
)
async def get_system_metrics() -> SystemMetricsCollection:
    """
    Collect and return current system metrics (CPU, memory, disk, network).
    
    Returns:
        SystemMetricsCollection: Current system metrics
        
    Raises:
        HTTPException: If metrics collection fails
    """
    try:
        collector = SystemCollector()
        metrics = collector.collect(instance_id=settings.agent_id)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect system metrics: {str(e)}"
        )


@router.get(
    "/metrics/cpu",
    status_code=status.HTTP_200_OK,
    summary="Get CPU metrics only"
)
async def get_cpu_metrics() -> dict:
    """
    Get CPU metrics only.
    
    Returns:
        dict: CPU metrics
    """
    try:
        collector = SystemCollector()
        cpu_metrics = collector.collect_cpu_metrics()
        return cpu_metrics.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect CPU metrics: {str(e)}"
        )


@router.get(
    "/metrics/memory",
    status_code=status.HTTP_200_OK,
    summary="Get memory metrics only"
)
async def get_memory_metrics() -> dict:
    """
    Get memory metrics only.
    
    Returns:
        dict: Memory metrics
    """
    try:
        collector = SystemCollector()
        memory_metrics = collector.collect_memory_metrics()
        return memory_metrics.model_dump()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect memory metrics: {str(e)}"
        )


@router.get(
    "/metrics/disk",
    status_code=status.HTTP_200_OK,
    summary="Get disk metrics only"
)
async def get_disk_metrics() -> dict:
    """
    Get disk metrics only.
    
    Returns:
        dict: Disk metrics
    """
    try:
        collector = SystemCollector()
        disk_metrics = collector.collect_disk_metrics()
        if disk_metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect disk metrics"
            )
        return disk_metrics.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect disk metrics: {str(e)}"
        )


@router.get(
    "/metrics/network",
    status_code=status.HTTP_200_OK,
    summary="Get network metrics only"
)
async def get_network_metrics() -> dict:
    """
    Get network metrics only.
    
    Returns:
        dict: Network metrics
    """
    try:
        collector = SystemCollector()
        network_metrics = collector.collect_network_metrics()
        if network_metrics is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to collect network metrics"
            )
        return network_metrics.model_dump()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to collect network metrics: {str(e)}"
        )
