"""
Notification API Routes.

Endpoints for in-app notification management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import logging

from src.auth.dependencies import get_api_key_or_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/notifications")


# Enums
class NotificationType(str, Enum):
    """Notification types."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class NotificationCategory(str, Enum):
    """Notification categories."""
    RECOMMENDATION = "recommendation"
    EXECUTION = "execution"
    COST_ALERT = "cost_alert"
    SYSTEM = "system"


# Request/Response Models
class NotificationResponse(BaseModel):
    """Notification response."""
    id: str = Field(..., description="Notification ID")
    customer_id: str = Field(..., description="Customer ID")
    type: NotificationType = Field(..., description="Notification type")
    category: NotificationCategory = Field(..., description="Notification category")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    is_read: bool = Field(False, description="Whether notification is read")
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")
    action_url: Optional[str] = Field(None, description="Action URL")
    metadata: Optional[dict] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "notif-123",
                "customer_id": "cust-123",
                "type": "warning",
                "category": "cost_alert",
                "title": "Cost Spike Detected",
                "message": "Your AWS costs increased by 45% in the last 24 hours",
                "is_read": False,
                "created_at": "2025-10-23T10:00:00Z",
                "read_at": None,
                "action_url": "/analysis/anomalies",
                "metadata": {
                    "cost_increase": 45.2,
                    "affected_services": ["EC2", "RDS"]
                }
            }
        }


@router.get(
    "/list",
    response_model=List[NotificationResponse],
    summary="List Notifications",
    description="List notifications for the authenticated customer"
)
async def list_notifications(
    unread_only: bool = False,
    category: Optional[NotificationCategory] = None,
    limit: int = 50,
    offset: int = 0,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    List notifications for the authenticated customer.
    
    - **unread_only**: Only return unread notifications (default False)
    - **category**: Filter by category (optional)
    - **limit**: Maximum number to return (default 50)
    - **offset**: Pagination offset (default 0)
    
    Returns list of notifications.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.debug(
            f"Listing notifications for customer {customer_id} "
            f"(unread_only: {unread_only}, category: {category}, limit: {limit})"
        )
        
        # TODO: Query notifications from database
        # For now, return mock data
        
        mock_notifications = [
            NotificationResponse(
                id="notif-1",
                customer_id=customer_id,
                type=NotificationType.WARNING,
                category=NotificationCategory.COST_ALERT,
                title="Cost Spike Detected",
                message="Your AWS costs increased by 45% in the last 24 hours",
                is_read=False,
                created_at=datetime.utcnow(),
                read_at=None,
                action_url="/analysis/anomalies",
                metadata={"cost_increase": 45.2}
            ),
            NotificationResponse(
                id="notif-2",
                customer_id=customer_id,
                type=NotificationType.SUCCESS,
                category=NotificationCategory.EXECUTION,
                title="Optimization Completed",
                message="Successfully migrated 5 instances to spot, saving $1,200/month",
                is_read=True,
                created_at=datetime.utcnow(),
                read_at=datetime.utcnow(),
                action_url="/execution/history",
                metadata={"savings": 1200}
            )
        ]
        
        # Filter by unread_only
        if unread_only:
            mock_notifications = [n for n in mock_notifications if not n.is_read]
        
        # Filter by category
        if category:
            mock_notifications = [n for n in mock_notifications if n.category == category]
        
        return mock_notifications[:limit]
        
    except Exception as e:
        logger.error(f"List notifications failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notifications: {str(e)}"
        )


@router.post(
    "/mark-read",
    summary="Mark Notifications as Read",
    description="Mark one or more notifications as read"
)
async def mark_notifications_read(
    notification_ids: List[str],
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Mark notifications as read.
    
    - **notification_ids**: List of notification IDs to mark as read
    
    Returns count of notifications marked as read.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.info(
            f"Marking {len(notification_ids)} notifications as read for customer {customer_id}"
        )
        
        # TODO: Update notifications in database
        
        return {
            "message": f"Marked {len(notification_ids)} notifications as read",
            "count": len(notification_ids)
        }
        
    except Exception as e:
        logger.error(f"Mark notifications read failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notifications as read: {str(e)}"
        )


@router.post(
    "/mark-all-read",
    summary="Mark All Notifications as Read",
    description="Mark all notifications as read for the authenticated customer"
)
async def mark_all_notifications_read(
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Mark all notifications as read for the authenticated customer.
    
    Returns count of notifications marked as read.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.info(f"Marking all notifications as read for customer {customer_id}")
        
        # TODO: Update all notifications in database
        
        return {
            "message": "Marked all notifications as read",
            "count": 0  # TODO: Return actual count
        }
        
    except Exception as e:
        logger.error(f"Mark all notifications read failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )


@router.delete(
    "/{notification_id}",
    summary="Delete Notification",
    description="Delete a notification"
)
async def delete_notification(
    notification_id: str,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Delete a notification.
    
    - **notification_id**: Notification ID to delete
    
    This action cannot be undone.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.info(f"Deleting notification {notification_id} for customer {customer_id}")
        
        # TODO: Delete notification from database
        
        return {"message": f"Notification {notification_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Delete notification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )


@router.get(
    "/unread-count",
    summary="Get Unread Count",
    description="Get count of unread notifications"
)
async def get_unread_count(
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Get count of unread notifications for the authenticated customer.
    
    Returns count of unread notifications by category.
    """
    try:
        customer_id = auth_info["customer_id"]
        logger.debug(f"Getting unread count for customer {customer_id}")
        
        # TODO: Query unread count from database
        
        return {
            "total": 5,
            "by_category": {
                "recommendation": 2,
                "execution": 1,
                "cost_alert": 2,
                "system": 0
            }
        }
        
    except Exception as e:
        logger.error(f"Get unread count failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get unread count: {str(e)}"
        )
