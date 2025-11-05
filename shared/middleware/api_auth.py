"""
API Key Authentication Middleware

Validates API keys for agent-to-agent communication.
"""

import hashlib
import secrets
from typing import Optional, Set
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class APIKeyManager:
    """Manages API keys for authentication."""
    
    def __init__(self):
        """Initialize API key manager."""
        self.valid_keys: Set[str] = set()
        self.key_hashes: Set[str] = set()
    
    def generate_key(self) -> str:
        """
        Generate a new API key.
        
        Returns:
            New API key
        """
        key = secrets.token_urlsafe(32)
        self.add_key(key)
        return key
    
    def add_key(self, key: str):
        """
        Add an API key.
        
        Args:
            key: API key to add
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self.valid_keys.add(key)
        self.key_hashes.add(key_hash)
    
    def validate_key(self, key: Optional[str]) -> bool:
        """
        Validate an API key.
        
        Args:
            key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not key:
            return False
        
        # Check direct match (for development)
        if key in self.valid_keys:
            return True
        
        # Check hash match (for production)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key_hash in self.key_hashes
    
    def revoke_key(self, key: str):
        """
        Revoke an API key.
        
        Args:
            key: API key to revoke
        """
        self.valid_keys.discard(key)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        self.key_hashes.discard(key_hash)


# Global API key manager
api_key_manager = APIKeyManager()


async def api_key_middleware(request: Request, call_next):
    """
    API key authentication middleware.
    
    Args:
        request: FastAPI request
        call_next: Next middleware/handler
        
    Returns:
        Response or 401 Unauthorized
    """
    # Skip authentication for health checks and public endpoints
    public_paths = ["/health", "/docs", "/openapi.json", "/redoc"]
    if any(request.url.path.startswith(path) for path in public_paths):
        return await call_next(request)
    
    # Get API key from header
    api_key = request.headers.get("X-API-Key")
    
    # Validate API key
    if not api_key_manager.validate_key(api_key):
        logger.warning(f"Invalid API key attempt from {request.client.host if request.client else 'unknown'}")
        return JSONResponse(
            status_code=401,
            content={
                "error": "Unauthorized",
                "message": "Invalid or missing API key"
            },
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    response = await call_next(request)
    return response
