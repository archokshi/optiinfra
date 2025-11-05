"""
API Key Authentication.

Manages API key generation, validation, and storage.
"""

import secrets
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class APIKey:
    """API Key data class (temporary until we have proper ORM models)."""
    
    def __init__(
        self,
        id: str,
        customer_id: str,
        name: str,
        key_hash: str,
        is_active: bool = True,
        created_at: datetime = None,
        expires_at: datetime = None,
        last_used_at: datetime = None,
        requests_count: int = 0
    ):
        self.id = id
        self.customer_id = customer_id
        self.name = name
        self.key_hash = key_hash
        self.is_active = is_active
        self.created_at = created_at or datetime.utcnow()
        self.expires_at = expires_at
        self.last_used_at = last_used_at
        self.requests_count = requests_count


class APIKeyManager:
    """Manages API keys."""
    
    # In-memory storage for now (will be replaced with database)
    _keys_storage: Dict[str, APIKey] = {}
    _hash_to_id: Dict[str, str] = {}
    
    @staticmethod
    def generate_key(prefix: str = "sk") -> str:
        """Generate a new API key."""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    async def create_key(
        customer_id: str,
        name: str,
        expires_days: int = 365,
        db: Any = None
    ) -> tuple[str, APIKey]:
        """
        Create a new API key.
        
        Args:
            customer_id: Customer ID
            name: Key name/description
            expires_days: Days until expiration
            db: Database session (optional, for future use)
        
        Returns:
            Tuple of (plain_key, APIKey object)
        """
        # Generate key
        plain_key = APIKeyManager.generate_key()
        hashed_key = APIKeyManager.hash_key(plain_key)
        
        # Create API key object
        key_id = f"key-{uuid.uuid4().hex[:12]}"
        api_key = APIKey(
            id=key_id,
            customer_id=customer_id,
            name=name,
            key_hash=hashed_key,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            is_active=True,
            requests_count=0
        )
        
        # Store in memory (temporary)
        APIKeyManager._keys_storage[key_id] = api_key
        APIKeyManager._hash_to_id[hashed_key] = key_id
        
        logger.info(f"Created API key {key_id} for customer {customer_id}")
        
        return plain_key, api_key
    
    @staticmethod
    async def validate_key(
        api_key: str,
        db: Any = None
    ) -> Optional[APIKey]:
        """
        Validate an API key.
        
        Args:
            api_key: Plain API key
            db: Database session (optional, for future use)
        
        Returns:
            APIKey object if valid, None otherwise
        """
        hashed_key = APIKeyManager.hash_key(api_key)
        
        # Look up in memory storage
        key_id = APIKeyManager._hash_to_id.get(hashed_key)
        if not key_id:
            logger.warning(f"API key not found: {api_key[:10]}...")
            return None
        
        key_record = APIKeyManager._keys_storage.get(key_id)
        if not key_record:
            return None
        
        # Check if active
        if not key_record.is_active:
            logger.warning(f"API key {key_id} is inactive")
            return None
        
        # Check if expired
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            logger.warning(f"API key {key_id} has expired")
            return None
        
        # Update last used
        key_record.last_used_at = datetime.utcnow()
        key_record.requests_count += 1
        
        logger.debug(f"Validated API key {key_id} for customer {key_record.customer_id}")
        
        return key_record
    
    @staticmethod
    async def list_keys(
        customer_id: str,
        db: Any = None
    ) -> list[APIKey]:
        """
        List all API keys for a customer.
        
        Args:
            customer_id: Customer ID
            db: Database session (optional, for future use)
        
        Returns:
            List of APIKey objects
        """
        keys = [
            key for key in APIKeyManager._keys_storage.values()
            if key.customer_id == customer_id
        ]
        return keys
    
    @staticmethod
    async def revoke_key(
        key_id: str,
        db: Any = None
    ) -> bool:
        """
        Revoke an API key.
        
        Args:
            key_id: Key ID
            db: Database session (optional, for future use)
        
        Returns:
            True if revoked, False if not found
        """
        key_record = APIKeyManager._keys_storage.get(key_id)
        if not key_record:
            return False
        
        key_record.is_active = False
        logger.info(f"Revoked API key {key_id}")
        
        return True
    
    @staticmethod
    async def delete_key(
        key_id: str,
        db: Any = None
    ) -> bool:
        """
        Delete an API key.
        
        Args:
            key_id: Key ID
            db: Database session (optional, for future use)
        
        Returns:
            True if deleted, False if not found
        """
        key_record = APIKeyManager._keys_storage.get(key_id)
        if not key_record:
            return False
        
        # Remove from storage
        del APIKeyManager._keys_storage[key_id]
        del APIKeyManager._hash_to_id[key_record.key_hash]
        
        logger.info(f"Deleted API key {key_id}")
        
        return True
