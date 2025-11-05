"""
Application API Routes V2 - Using ClickHouse Readers
Phase 6.5: Application Agent Refactor
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime
import logging

from ..readers.application_reader import ApplicationReader
from ..integration.data_collector_client import DataCollectorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/applications", tags=["applications-v2"])


@router.get("/{customer_id}/{provider}/quality")
async def get_quality_metrics(
    customer_id: str,
    provider: str,
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    application_id: Optional[str] = Query(None, description="Filter by application ID")
):
    """
    Get quality metrics from ClickHouse
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        start_date: Optional start date
        end_date: Optional end date
        application_id: Optional application ID filter
    
    Returns:
        List of quality metrics
    """
    try:
        reader = ApplicationReader()
        
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        metrics = reader.get_quality_metrics(
            customer_id=customer_id,
            provider=provider,
            start_date=start_dt,
            end_date=end_dt,
            application_id=application_id
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "metrics": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get quality metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/hallucinations")
async def get_hallucination_metrics(
    customer_id: str,
    provider: str,
    hours: int = Query(24, description="Hours to look back"),
    threshold: float = Query(0.5, description="Minimum hallucination score")
):
    """
    Get hallucination detection metrics
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        hours: Number of hours to look back
        threshold: Minimum hallucination score to include
    
    Returns:
        List of hallucination metrics
    """
    try:
        reader = ApplicationReader()
        
        metrics = reader.get_hallucination_metrics(
            customer_id=customer_id,
            provider=provider,
            hours=hours,
            threshold=threshold
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period_hours": hours,
            "threshold": threshold,
            "hallucinations": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get hallucination metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/toxicity")
async def get_toxicity_metrics(
    customer_id: str,
    provider: str,
    hours: int = Query(24, description="Hours to look back"),
    threshold: float = Query(0.3, description="Minimum toxicity score")
):
    """
    Get toxicity/safety metrics
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        hours: Number of hours to look back
        threshold: Minimum toxicity score to include
    
    Returns:
        List of toxicity metrics
    """
    try:
        reader = ApplicationReader()
        
        metrics = reader.get_toxicity_metrics(
            customer_id=customer_id,
            provider=provider,
            hours=hours,
            threshold=threshold
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period_hours": hours,
            "threshold": threshold,
            "toxic_content": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get toxicity metrics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/summary")
async def get_application_summary(
    customer_id: str,
    provider: str
):
    """
    Get application quality summary
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
    
    Returns:
        Application summary
    """
    try:
        reader = ApplicationReader()
        
        summary = reader.get_application_summary(
            customer_id=customer_id,
            provider=provider
        )
        
        reader.close()
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get application summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/models")
async def get_model_performance(
    customer_id: str,
    provider: str,
    hours: int = Query(24, description="Hours to look back")
):
    """
    Get performance metrics by model
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        hours: Number of hours to look back
    
    Returns:
        Model performance metrics
    """
    try:
        reader = ApplicationReader()
        
        metrics = reader.get_model_performance(
            customer_id=customer_id,
            provider=provider,
            hours=hours
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period_hours": hours,
            "models": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to get model performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-collection")
async def trigger_collection(
    customer_id: str,
    provider: str,
    async_mode: bool = True
):
    """
    Trigger application data collection
    
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
            data_types=["application"],
            async_mode=async_mode
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to trigger collection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
