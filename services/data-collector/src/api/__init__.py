"""API endpoints for data-collector service"""

from .credentials import router as credentials_router

__all__ = ["credentials_router"]
