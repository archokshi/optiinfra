"""
JWT Token Handler.

Handles JWT token creation and validation.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os
import logging

logger = logging.getLogger(__name__)

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "optiinfra-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class JWTHandler:
    """Handle JWT token operations."""
    
    @staticmethod
    def create_token(
        data: Dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT token.
        
        Args:
            data: Data to encode in token
            expires_delta: Optional expiration time delta
        
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        logger.debug(f"Created JWT token for subject: {data.get('sub')}")
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """
        Decode and validate JWT token.
        
        Args:
            token: JWT token to decode
        
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.debug(f"Decoded JWT token for subject: {payload.get('sub')}")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except Exception as e:
            logger.warning(f"JWT validation error: {e}")
            return None
    
    @staticmethod
    def create_access_token(
        subject: str,
        customer_id: str,
        additional_claims: Optional[Dict] = None
    ) -> str:
        """
        Create access token with standard claims.
        
        Args:
            subject: Token subject (usually username or user ID)
            customer_id: Customer ID
            additional_claims: Optional additional claims
        
        Returns:
            JWT access token
        """
        data = {
            "sub": subject,
            "customer_id": customer_id,
            "type": "access"
        }
        
        if additional_claims:
            data.update(additional_claims)
        
        return JWTHandler.create_token(data)
    
    @staticmethod
    def create_refresh_token(
        subject: str,
        customer_id: str
    ) -> str:
        """
        Create refresh token.
        
        Args:
            subject: Token subject
            customer_id: Customer ID
        
        Returns:
            JWT refresh token
        """
        data = {
            "sub": subject,
            "customer_id": customer_id,
            "type": "refresh"
        }
        
        # Refresh tokens last longer
        expires_delta = timedelta(days=30)
        
        return JWTHandler.create_token(data, expires_delta)
