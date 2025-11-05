"""
Resource API Routes V2 - Using ClickHouse Readers
Phase 6.5: Resource Agent Refactor
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from ..readers.resource_reader import ResourceReader
from ..integration.data_collector_client import DataCollectorClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/resources", tags=["resources-v2"])


@router.get("/{customer_id}/{provider}/inventory")
async def get_resource_inventory(
    customer_id: str,
    provider: str,
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    region: Optional[str] = Query(None, description="Filter by region")
):
    """
    Get resource inventory from ClickHouse
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider (vultr, aws, gcp, azure)
        resource_type: Optional resource type filter
        status: Optional status filter
        region: Optional region filter
    
    Returns:
        List of resources
    """
    try:
        reader = ResourceReader()
        
        inventory = reader.get_inventory(
            customer_id=customer_id,
            provider=provider,
            resource_type=resource_type,
            status=status,
            region=region
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "resources": inventory,
            "count": len(inventory)
        }
        
    except Exception as e:
        logger.error(f"Failed to get resource inventory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/changes")
async def get_resource_changes(
    customer_id: str,
    provider: str,
    hours: int = Query(24, description="Hours to look back")
):
    """
    Get resource changes over time period
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        hours: Number of hours to look back
    
    Returns:
        List of resource changes
    """
    try:
        reader = ResourceReader()
        
        changes = reader.get_resource_changes(
            customer_id=customer_id,
            provider=provider,
            hours=hours
        )
        
        reader.close()
        
        return {
            "customer_id": customer_id,
            "provider": provider,
            "period_hours": hours,
            "changes": changes,
            "count": len(changes)
        }
        
    except Exception as e:
        logger.error(f"Failed to get resource changes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/summary")
async def get_resource_summary(
    customer_id: str,
    provider: str
):
    """
    Get resource summary for a provider
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
    
    Returns:
        Resource summary
    """
    try:
        reader = ResourceReader()
        
        summary = reader.get_resource_summary(
            customer_id=customer_id,
            provider=provider
        )
        
        reader.close()
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to get resource summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/{provider}/resource/{resource_id}")
async def get_resource_details(
    customer_id: str,
    provider: str,
    resource_id: str
):
    """
    Get specific resource details
    
    Args:
        customer_id: Customer UUID
        provider: Cloud provider
        resource_id: Resource identifier
    
    Returns:
        Resource details
    """
    try:
        reader = ResourceReader()
        
        resource = reader.get_resource_by_id(
            customer_id=customer_id,
            provider=provider,
            resource_id=resource_id
        )
        
        reader.close()
        
        if not resource:
            raise HTTPException(status_code=404, detail="Resource not found")
        
        return resource
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get resource details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-collection")
async def trigger_collection(
    customer_id: str,
    provider: str,
    async_mode: bool = True
):
    """
    Trigger resource data collection
    
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
            data_types=["resource"],
            async_mode=async_mode
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to trigger collection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
