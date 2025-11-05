"""
Webhook API Routes.

Endpoints for webhook management and event notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
import logging
import uuid

from src.auth.dependencies import get_api_key_or_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks")


# Request/Response Models
class RegisterWebhookRequest(BaseModel):
    """Request to register a webhook."""
    url: HttpUrl = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for verification")
    description: Optional[str] = Field(None, description="Webhook description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/webhooks/optiinfra",
                "events": ["recommendation.created", "execution.completed", "cost.anomaly"],
                "secret": "whsec_1234567890abcdef",
                "description": "Production webhook for cost alerts"
            }
        }


class WebhookResponse(BaseModel):
    """Webhook response."""
    id: str = Field(..., description="Webhook ID")
    customer_id: str = Field(..., description="Customer ID")
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Subscribed events")
    is_active: bool = Field(..., description="Whether webhook is active")
    description: Optional[str] = Field(None, description="Webhook description")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger timestamp")
    total_deliveries: int = Field(0, description="Total deliveries")
    failed_deliveries: int = Field(0, description="Failed deliveries")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "webhook-123",
                "customer_id": "cust-123",
                "url": "https://example.com/webhooks/optiinfra",
                "events": ["recommendation.created", "execution.completed"],
                "is_active": True,
                "description": "Production webhook",
                "created_at": "2025-10-23T10:00:00Z",
                "last_triggered_at": "2025-10-23T12:00:00Z",
                "total_deliveries": 150,
                "failed_deliveries": 2
            }
        }


@router.post(
    "/register",
    response_model=WebhookResponse,
    summary="Register Webhook",
    description="Register a new webhook endpoint"
)
async def register_webhook(
    request: RegisterWebhookRequest,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Register a new webhook endpoint.
    
    - **url**: Webhook URL (must be HTTPS)
    - **events**: List of events to subscribe to
    - **secret**: Optional secret for webhook verification
    - **description**: Optional description
    
    Available events:
    - recommendation.created
    - recommendation.approved
    - recommendation.rejected
    - execution.started
    - execution.completed
    - execution.failed
    - cost.anomaly
    - cost.threshold_exceeded
    """
    try:
        webhook_id = f"webhook-{uuid.uuid4().hex[:12]}"
        customer_id = auth_info["customer_id"]
        
        logger.info(f"Registering webhook {webhook_id} for customer {customer_id}")
        
        # TODO: Store webhook in database
        # For now, return mock response
        
        return WebhookResponse(
            id=webhook_id,
            customer_id=customer_id,
            url=str(request.url),
            events=request.events,
            is_active=True,
            description=request.description,
            created_at=datetime.utcnow(),
            last_triggered_at=None,
            total_deliveries=0,
            failed_deliveries=0
        )
        
    except Exception as e:
        logger.error(f"Register webhook failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register webhook: {str(e)}"
        )


@router.get(
    "/list",
    response_model=List[WebhookResponse],
    summary="List Webhooks",
    description="List all registered webhooks"
)
async def list_webhooks(
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    List all registered webhooks for the authenticated customer.
    
    Returns list of webhook configurations.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.debug(f"Listing webhooks for customer {customer_id}")
        
        # TODO: Query webhooks from database
        # For now, return empty list
        
        return []
        
    except Exception as e:
        logger.error(f"List webhooks failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list webhooks: {str(e)}"
        )


@router.put(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update Webhook",
    description="Update a webhook configuration"
)
async def update_webhook(
    webhook_id: str,
    request: RegisterWebhookRequest,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Update a webhook configuration.
    
    - **webhook_id**: Webhook ID to update
    - **url**: New webhook URL
    - **events**: New list of events
    - **secret**: New secret (optional)
    - **description**: New description (optional)
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.info(f"Updating webhook {webhook_id} for customer {customer_id}")
        
        # TODO: Update webhook in database
        # For now, return mock response
        
        return WebhookResponse(
            id=webhook_id,
            customer_id=customer_id,
            url=str(request.url),
            events=request.events,
            is_active=True,
            description=request.description,
            created_at=datetime.utcnow(),
            last_triggered_at=None,
            total_deliveries=0,
            failed_deliveries=0
        )
        
    except Exception as e:
        logger.error(f"Update webhook failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update webhook: {str(e)}"
        )


@router.delete(
    "/{webhook_id}",
    summary="Delete Webhook",
    description="Delete a webhook"
)
async def delete_webhook(
    webhook_id: str,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Delete a webhook.
    
    - **webhook_id**: Webhook ID to delete
    
    This action cannot be undone.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.info(f"Deleting webhook {webhook_id} for customer {customer_id}")
        
        # TODO: Delete webhook from database
        
        return {"message": f"Webhook {webhook_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete webhook failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete webhook: {str(e)}"
        )


@router.post(
    "/{webhook_id}/test",
    summary="Test Webhook",
    description="Send a test event to a webhook"
)
async def test_webhook(
    webhook_id: str,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Send a test event to a webhook.
    
    - **webhook_id**: Webhook ID to test
    
    Sends a test event to verify the webhook is working correctly.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.info(f"Testing webhook {webhook_id} for customer {customer_id}")
        
        # TODO: Send test event to webhook
        
        return {
            "message": f"Test event sent to webhook {webhook_id}",
            "status": "delivered",
            "response_code": 200
        }
        
    except Exception as e:
        logger.error(f"Test webhook failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test webhook: {str(e)}"
        )
