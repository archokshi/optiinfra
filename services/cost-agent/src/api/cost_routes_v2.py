"""
Cost Routes V2 - Using ClickHouse Readers
Phase 6.3: Cost Agent Refactor

New API endpoints that read from ClickHouse instead of calling cloud APIs directly
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import logging

from ..readers import CostReader
from ..integration import DataCollectorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/costs", tags=["costs-v2"])


# Request/Response Models
class TriggerCollectionRequest(BaseModel):
    customer_id: str
    provider: str
    data_types: Optional[List[str]] = ["cost"]


class TriggerCollectionResponse(BaseModel):
    task_id: str
    status: str
    message: str


@router.get("/{customer_id}/{provider}/metrics")
async def get_cost_metrics(
    customer_id: str,
    provider: str,
    days: int = Query(default=30, ge=1, le=365),
    metric_type: Optional[str] = None
):
    """
    Get cost metrics from ClickHouse
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider (vultr, aws, gcp, azure)
        days: Number of days to look back (default: 30)
        metric_type: Optional filter by metric type
    
    Returns:
        List of cost metrics
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        with CostReader() as reader:
            metrics = reader.get_cost_metrics(
                customer_id=customer_id,
                provider=provider,
                start_date=start_date,
                end_date=end_date,
                metric_type=metric_type
            )
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "metric_count": len(metrics),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/latest")
async def get_latest_costs(
    customer_id: str,
    provider: str,
    limit: int = Query(default=100, ge=1, le=1000)
):
    """
    Get the most recent cost metrics
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        limit: Maximum number of records (default: 100)
    
    Returns:
        List of latest cost metrics
    """
    try:
        with CostReader() as reader:
            metrics = reader.get_latest_costs(
                customer_id=customer_id,
                provider=provider,
                limit=limit
            )
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "limit": limit,
            "metric_count": len(metrics),
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get latest costs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/trends")
async def get_cost_trends(
    customer_id: str,
    provider: str,
    days: int = Query(default=30, ge=1, le=365),
    group_by: str = Query(default="day", regex="^(day|week|month)$")
):
    """
    Get cost trends aggregated by time period
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        days: Number of days to look back (default: 30)
        group_by: Grouping period (day, week, month)
    
    Returns:
        List of aggregated cost trends
    """
    try:
        with CostReader() as reader:
            trends = reader.get_cost_trends(
                customer_id=customer_id,
                provider=provider,
                days=days,
                group_by=group_by
            )
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period": {
                "days": days,
                "group_by": group_by
            },
            "trend_count": len(trends),
            "trends": trends
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/by-resource")
async def get_cost_by_resource(
    customer_id: str,
    provider: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get costs grouped by resource
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        days: Number of days to look back (default: 30)
    
    Returns:
        List of costs grouped by resource
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        with CostReader() as reader:
            costs = reader.get_cost_by_resource(
                customer_id=customer_id,
                provider=provider,
                start_date=start_date,
                end_date=end_date
            )
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "resource_count": len(costs),
            "costs_by_resource": costs
        }
        
    except Exception as e:
        logger.error(f"Failed to get costs by resource: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/by-type")
async def get_cost_by_type(
    customer_id: str,
    provider: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get costs grouped by metric type
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        days: Number of days to look back (default: 30)
    
    Returns:
        List of costs grouped by type
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        with CostReader() as reader:
            costs = reader.get_cost_by_type(
                customer_id=customer_id,
                provider=provider,
                start_date=start_date,
                end_date=end_date
            )
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "type_count": len(costs),
            "costs_by_type": costs
        }
        
    except Exception as e:
        logger.error(f"Failed to get costs by type: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/total")
async def get_total_cost(
    customer_id: str,
    provider: str,
    days: int = Query(default=30, ge=1, le=365)
):
    """
    Get total cost for a period
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        days: Number of days to look back (default: 30)
    
    Returns:
        Total cost summary
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        end_date = datetime.now()
        
        with CostReader() as reader:
            total = reader.get_total_cost(
                customer_id=customer_id,
                provider=provider,
                start_date=start_date,
                end_date=end_date
            )
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "total_cost": total.get("total_cost", 0),
            "currency": total.get("currency", "USD"),
            "metric_count": total.get("metric_count", 0),
            "unique_resources": total.get("unique_resources", 0),
            "first_metric": total.get("first_metric"),
            "last_metric": total.get("last_metric")
        }
        
    except Exception as e:
        logger.error(f"Failed to get total cost: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-collection", response_model=TriggerCollectionResponse)
async def trigger_collection(request: TriggerCollectionRequest):
    """
    Trigger data collection via data-collector service
    
    This proxies the request to the data-collector service
    
    Args:
        request: Collection request with customer_id, provider, data_types
    
    Returns:
        Task ID and status
    """
    try:
        client = DataCollectorClient()
        result = client.trigger_collection(
            customer_id=request.customer_id,
            provider=request.provider,
            data_types=request.data_types,
            async_mode=True
        )
        
        if "error" in result:
            raise HTTPException(status_code=503, detail=result.get("message", "Service unavailable"))
        
        return TriggerCollectionResponse(
            task_id=result.get("task_id", ""),
            status=result.get("status", "unknown"),
            message=result.get("message", "Collection triggered")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger collection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection-status/{task_id}")
async def get_collection_status(task_id: str):
    """
    Get the status of a collection task
    
    Args:
        task_id: Task ID from trigger_collection
    
    Returns:
        Task status and details
    """
    try:
        client = DataCollectorClient()
        result = client.get_collection_status(task_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result.get("message", "Task not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/collection-history")
async def get_collection_history(
    customer_id: str,
    limit: int = Query(default=10, ge=1, le=100)
):
    """
    Get collection history for a customer
    
    Args:
        customer_id: Customer UUID
        limit: Maximum number of records (default: 10)
    
    Returns:
        List of collection history records
    """
    try:
        client = DataCollectorClient()
        history = client.get_collection_history(customer_id, limit)
        
        return {
            "customer_id": customer_id,
            "limit": limit,
            "history_count": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"Failed to get collection history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
