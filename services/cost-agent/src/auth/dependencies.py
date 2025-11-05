"""
Authentication Dependencies.

FastAPI dependencies for authentication.
"""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from src.auth.api_key import APIKeyManager, APIKey
from src.auth.jwt_handler import JWTHandler

logger = logging.getLogger(__name__)

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> APIKey:
    """
    Validate API key from header.
    
    Args:
        api_key: API key from X-API-Key header
    
    Returns:
        APIKey object if valid
    
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not api_key:
        logger.warning("API key missing from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    key_record = await APIKeyManager.validate_key(api_key)
    
    if not key_record:
        logger.warning(f"Invalid API key: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    return key_record


async def get_optional_api_key(
    api_key: Optional[str] = Security(api_key_header)
) -> Optional[APIKey]:
    """
    Optionally validate API key.
    
    Args:
        api_key: API key from X-API-Key header
    
    Returns:
        APIKey object if valid, None if not provided
    """
    if not api_key:
        return None
    
    key_record = await APIKeyManager.validate_key(api_key)
    return key_record


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> dict:
    """
    Validate JWT token from Authorization header.
    
    Args:
        credentials: Bearer token credentials
    
    Returns:
        Token payload if valid
    
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        logger.warning("Bearer token missing from request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Include Authorization: Bearer <token> header.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    payload = JWTHandler.decode_token(credentials.credentials)
    
    if not payload:
        logger.warning("Invalid JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return payload


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[dict]:
    """
    Optionally validate JWT token.
    
    Args:
        credentials: Bearer token credentials
    
    Returns:
        Token payload if valid, None if not provided
    """
    if not credentials:
        return None
    
    payload = JWTHandler.decode_token(credentials.credentials)
    return payload


async def get_api_key_or_token(
    api_key: Optional[str] = Security(api_key_header),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> dict:
    """
    Accept either API key or JWT token.
    
    Args:
        api_key: API key from X-API-Key header
        credentials: Bearer token credentials
    
    Returns:
        Authentication info (customer_id, auth_type, etc.)
    
    Raises:
        HTTPException: If neither authentication method is provided or valid
    """
    # Try API key first
    if api_key:
        key_record = await APIKeyManager.validate_key(api_key)
        if key_record:
            return {
                "customer_id": key_record.customer_id,
                "auth_type": "api_key",
                "key_id": key_record.id,
                "key_name": key_record.name
            }
    
    # Try JWT token
    if credentials:
        payload = JWTHandler.decode_token(credentials.credentials)
        if payload:
            return {
                "customer_id": payload.get("customer_id"),
                "auth_type": "jwt",
                "subject": payload.get("sub"),
                "token_type": payload.get("type", "access")
            }
    
    # Neither worked
    logger.warning("No valid authentication provided")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either X-API-Key or Authorization: Bearer <token> header.",
        headers={"WWW-Authenticate": "ApiKey, Bearer"}
    )


def require_customer_id(customer_id: str):
    """
    Dependency factory to require specific customer ID.
    
    Args:
        customer_id: Required customer ID
    
    Returns:
        Dependency function
    """
    async def check_customer_id(
        auth_info: dict = Depends(get_api_key_or_token)
    ):
        if auth_info["customer_id"] != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. This resource belongs to customer {customer_id}"
            )
        return auth_info
    
    return check_customer_id
