"""
Authentication API Routes.

Endpoints for API key and JWT token management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging

from src.auth.api_key import APIKeyManager, APIKey
from src.auth.jwt_handler import JWTHandler
from src.auth.dependencies import get_api_key, get_api_key_or_token
from src.models.auth import (
    CreateAPIKeyRequest,
    APIKeyResponse,
    CreateTokenRequest,
    TokenResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth")


@router.post(
    "/api-key/create",
    response_model=APIKeyResponse,
    summary="Create API Key",
    description="Create a new API key for authentication"
)
async def create_api_key(
    request: CreateAPIKeyRequest
):
    """
    Create a new API key.
    
    - **customer_id**: Customer ID
    - **name**: Key name/description
    - **expires_days**: Days until expiration (default 365)
    
    Returns the API key (only shown once) and key metadata.
    """
    try:
        plain_key, key_record = await APIKeyManager.create_key(
            customer_id=request.customer_id,
            name=request.name,
            expires_days=request.expires_days or 365
        )
        
        logger.info(f"Created API key {key_record.id} for customer {request.customer_id}")
        
        return APIKeyResponse(
            id=key_record.id,
            key=plain_key,  # Only shown once!
            customer_id=key_record.customer_id,
            name=key_record.name,
            is_active=key_record.is_active,
            created_at=key_record.created_at,
            expires_at=key_record.expires_at,
            last_used_at=key_record.last_used_at,
            requests_count=key_record.requests_count
        )
    except Exception as e:
        logger.error(f"Failed to create API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )


@router.get(
    "/api-key/list",
    response_model=List[APIKeyResponse],
    summary="List API Keys",
    description="List all API keys for a customer"
)
async def list_api_keys(
    customer_id: str,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    List all API keys for a customer.
    
    - **customer_id**: Customer ID to list keys for
    
    Requires authentication with API key or JWT token.
    """
    # Verify customer ID matches authenticated customer
    if auth_info["customer_id"] != customer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Can only list your own API keys."
        )
    
    try:
        keys = await APIKeyManager.list_keys(customer_id)
        
        return [
            APIKeyResponse(
                id=key.id,
                key=None,  # Never return the actual key
                customer_id=key.customer_id,
                name=key.name,
                is_active=key.is_active,
                created_at=key.created_at,
                expires_at=key.expires_at,
                last_used_at=key.last_used_at,
                requests_count=key.requests_count
            )
            for key in keys
        ]
    except Exception as e:
        logger.error(f"Failed to list API keys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list API keys: {str(e)}"
        )


@router.post(
    "/api-key/{key_id}/revoke",
    summary="Revoke API Key",
    description="Revoke an API key (makes it inactive)"
)
async def revoke_api_key(
    key_id: str,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Revoke an API key.
    
    - **key_id**: Key ID to revoke
    
    The key will be marked as inactive but not deleted.
    """
    try:
        success = await APIKeyManager.revoke_key(key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {key_id} not found"
            )
        
        logger.info(f"Revoked API key {key_id}")
        
        return {"message": f"API key {key_id} revoked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to revoke API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke API key: {str(e)}"
        )


@router.delete(
    "/api-key/{key_id}",
    summary="Delete API Key",
    description="Permanently delete an API key"
)
async def delete_api_key(
    key_id: str,
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Delete an API key permanently.
    
    - **key_id**: Key ID to delete
    
    This action cannot be undone.
    """
    try:
        success = await APIKeyManager.delete_key(key_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key {key_id} not found"
            )
        
        logger.info(f"Deleted API key {key_id}")
        
        return {"message": f"API key {key_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete API key: {str(e)}"
        )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Create JWT Token",
    description="Create a JWT access token"
)
async def create_token(
    request: CreateTokenRequest
):
    """
    Create JWT token.
    
    - **username**: Username or email
    - **password**: Password
    
    Returns JWT access token for authentication.
    
    Note: This is a simplified implementation. In production, validate
    credentials against a user database.
    """
    # TODO: Validate credentials against user database
    # For now, accept any username/password for demo purposes
    
    try:
        # In production, validate credentials and get customer_id from database
        customer_id = "cust-demo"  # Placeholder
        
        token = JWTHandler.create_access_token(
            subject=request.username,
            customer_id=customer_id
        )
        
        logger.info(f"Created JWT token for user {request.username}")
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600  # 1 hour
        )
    except Exception as e:
        logger.error(f"Failed to create token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create token: {str(e)}"
        )


@router.post(
    "/token/refresh",
    response_model=TokenResponse,
    summary="Refresh JWT Token",
    description="Refresh an expired JWT token"
)
async def refresh_token(
    refresh_token: str
):
    """
    Refresh JWT token.
    
    - **refresh_token**: Refresh token
    
    Returns new access token.
    """
    try:
        # Decode refresh token
        payload = JWTHandler.decode_token(refresh_token)
        
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new access token
        new_token = JWTHandler.create_access_token(
            subject=payload["sub"],
            customer_id=payload["customer_id"]
        )
        
        logger.info(f"Refreshed token for user {payload['sub']}")
        
        return TokenResponse(
            access_token=new_token,
            token_type="bearer",
            expires_in=3600
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh token: {str(e)}"
        )


@router.get(
    "/me",
    summary="Get Current User",
    description="Get information about the authenticated user"
)
async def get_current_user_info(
    auth_info: dict = Depends(get_api_key_or_token)
):
    """
    Get information about the currently authenticated user.
    
    Returns authentication details based on the method used (API key or JWT).
    """
    return {
        "customer_id": auth_info["customer_id"],
        "auth_type": auth_info["auth_type"],
        **{k: v for k, v in auth_info.items() if k not in ["customer_id", "auth_type"]}
    }
