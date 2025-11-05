"""
API v1 Router.

Consolidates all v1 endpoints into a single router.
"""

from fastapi import APIRouter

# Import all route modules
from src.api import (
    health,
    analyze,
    aws_costs,
    gcp_costs,
    azure_costs,
    recommendation_routes,
    execution_routes,
    learning_routes,
    auth_routes,
    bulk_routes,
    webhook_routes,
    notification_routes
)

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers with appropriate tags
router.include_router(health.router, tags=["Health & Status"])
router.include_router(auth_routes.router, tags=["Authentication"])
router.include_router(aws_costs.router, prefix="/aws", tags=["AWS Costs"])
router.include_router(gcp_costs.router, tags=["GCP Costs"])
router.include_router(azure_costs.router, tags=["Azure Costs"])
router.include_router(analyze.router, tags=["Analysis"])
router.include_router(recommendation_routes.router, tags=["Recommendations"])
router.include_router(execution_routes.router, tags=["Execution"])
router.include_router(learning_routes.router, tags=["Learning Loop"])
router.include_router(bulk_routes.router, tags=["Bulk Operations"])
router.include_router(webhook_routes.router, tags=["Webhooks"])
router.include_router(notification_routes.router, tags=["Notifications"])

__all__ = ["router"]
