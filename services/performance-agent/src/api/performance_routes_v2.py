"""
Performance API Routes V2 - Using ClickHouse Readers
Phase 6.5: Performance Agent Refactor
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from datetime import datetime
import logging

from ..readers.performance_reader import PerformanceReader
from ..integration.data_collector_client import DataCollectorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/performance", tags=["performance-v2"])


@router.get("/{customer_id}/{provider}/metrics")
async def get_performance_metrics(
    customer_id: str,
    provider: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID")
):
    """
    Get performance metrics from ClickHouse
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider (vultr, aws, gcp, azure)
        start_date: Optional start date
        end_date: Optional end date
        metric_type: Optional metric type filter
        resource_id: Optional resource ID filter
    
    Returns:
        List of performance metrics
    """
    try:
        reader = PerformanceReader()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = reader.get_metrics(
            customer_id=customer_id,
            provider=provider,
            start_date=start_dt,
            end_date=end_dt,
            metric_type=metric_type,
            resource_id=resource_id
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "metrics": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/average")
async def get_average_metrics(
    customer_id: str,
    provider: str,
    hours: int = Query(24, description="Hours to look back")
):
    """
    Get average performance metrics over time period
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        hours: Number of hours to look back
    
    Returns:
        Aggregated performance metrics
    """
    try:
        reader = PerformanceReader()
        
        metrics = reader.get_average_metrics(
            customer_id=customer_id,
            provider=provider,
            hours=hours
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period_hours": hours,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get average metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/resource/{resource_id}")
async def get_resource_performance(
    customer_id: str,
    provider: str,
    resource_id: str,
    hours: int = Query(24, description="Hours to look back")
):
    """
    Get performance metrics for a specific resource
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        resource_id: Resource identifier
        hours: Number of hours to look back
    
    Returns:
        Resource performance metrics
    """
    try:
        reader = PerformanceReader()
        
        metrics = reader.get_resource_performance(
            customer_id=customer_id,
            provider=provider,
            resource_id=resource_id,
            hours=hours
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "resource_id": resource_id,
            "period_hours": hours,
            "metrics": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get resource performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/summary")
async def get_performance_summary(
    customer_id: str,
    provider: str
):
    """
    Get performance summary for a provider
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
    
    Returns:
        Performance summary
    """
    try:
        reader = PerformanceReader()
        
        summary = reader.get_performance_summary(
            customer_id=customer_id,
            provider=provider
        )
        
        reader.close()
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-collection")
async def trigger_collection(
    customer_id: str,
    provider: str,
    async_mode: bool = True
):
    """
    Trigger performance data collection
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        async_mode: Run collection asynchronously
    
    Returns:
        Collection task details
    """
    try:
        client = DataCollectorClient()
        
        result = await client.trigger_collection(
            customer_id=customer_id,
            provider=provider,
            data_types=["performance"],
            async_mode=async_mode
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to trigger collection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
