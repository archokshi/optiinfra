"""
Authentication Models.

Pydantic models for authentication requests and responses.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class CreateAPIKeyRequest(BaseModel):
    """Request to create a new API key."""
    
    customer_id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Key name/description")
    expires_days: Optional[int] = Field(365, description="Days until expiration")
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_id": "cust-123",
                "name": "Production API Key",
                "expires_days": 365
            }
        }


class APIKeyResponse(BaseModel):
    """API key response."""
    
    id: str = Field(..., description="Key ID")
    key: Optional[str] = Field(None, description="Plain API key (only shown once)")
    customer_id: str = Field(..., description="Customer ID")
    name: str = Field(..., description="Key name")
    is_active: bool = Field(..., description="Whether key is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    requests_count: int = Field(0, description="Total requests made with this key")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "key-abc123",
                "key": "sk_1234567890abcdef",
                "customer_id": "cust-123",
                "name": "Production API Key",
                "is_active": True,
                "created_at": "2025-10-23T10:00:00Z",
                "expires_at": "2026-10-23T10:00:00Z",
                "last_used_at": "2025-10-23T12:00:00Z",
                "requests_count": 1500
            }
        }


class CreateTokenRequest(BaseModel):
    """Request to create JWT token."""
    
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin@optiinfra.com",
                "password": "secure-password"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response."""
    
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Expiration time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class APIKeyInfo(BaseModel):
    """Information about the authenticated API key."""
    
    id: str
    customer_id: str
    name: str
    is_active: bool
    
    class Config:
        from_attributes = True
