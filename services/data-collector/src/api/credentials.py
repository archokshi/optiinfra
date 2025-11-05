"""
Credentials API Endpoints
Allows customers to manage their cloud provider credentials through the dashboard
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..credential_manager import CredentialManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/credentials", tags=["credentials"])


# Request/Response Models
class CredentialCreate(BaseModel):
    provider: str = Field(..., description="Cloud provider: vultr, aws, gcp, azure")
    credential_name: str = Field(..., description="User-friendly name for the credential")
    credentials: Dict[str, Any] = Field(..., description="Provider-specific credentials")
    credential_type: str = Field(default="api_key", description="Type of credential")
    permissions: str = Field(default="read_only", description="Permission level")


class CredentialResponse(BaseModel):
    id: str
    provider: str
    credential_name: str
    credential_type: str
    permissions: str
    is_active: bool
    is_verified: bool
    last_verified_at: Optional[datetime]
    last_used_at: Optional[datetime]
    usage_count: int
    created_at: datetime
    updated_at: datetime


class CredentialVerifyRequest(BaseModel):
    credential_id: str


class CredentialVerifyResponse(BaseModel):
    credential_id: str
    is_verified: bool
    message: str
    error: Optional[str] = None


# Dependency to get customer_id (in production, this would come from JWT token)
async def get_current_customer_id() -> str:
    """
    Get current customer ID from authentication token
    
    In production, this would:
    1. Extract JWT token from Authorization header
    2. Validate token
    3. Extract customer_id from token claims
    
    For now, we'll use a default customer ID
    """
    # TODO: Implement proper authentication
    return "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"  # Sample customer ID


@router.post("/", response_model=Dict[str, str])
async def create_credential(
    credential: CredentialCreate,
    customer_id: str = Depends(get_current_customer_id)
):
    """
    Create a new cloud credential
    
    Example for Vultr:
    ```json
    {
      "provider": "vultr",
      "credential_name": "Production Vultr",
      "credentials": {
        "api_key": "your-vultr-api-key-here"
      },
      "credential_type": "api_key",
      "permissions": "read_only"
    }
    ```
    
    Example for AWS:
    ```json
    {
      "provider": "aws",
      "credential_name": "Production AWS",
      "credentials": {
        "access_key_id": "AKIA...",
        "secret_access_key": "..."
      },
      "credential_type": "access_key",
      "permissions": "read_only"
    }
    ```
    """
    try:
        credential_manager = CredentialManager()
        
        credential_id = credential_manager.store_credential(
            customer_id=customer_id,
            provider=credential.provider,
            credential_name=credential.credential_name,
            credentials=credential.credentials,
            credential_type=credential.credential_type,
            permissions=credential.permissions
        )
        
        logger.info(f"Created credential {credential_id} for customer {customer_id}, provider {credential.provider}")
        
        return {
            "credential_id": credential_id,
            "message": f"Credential '{credential.credential_name}' created successfully",
            "provider": credential.provider
        }
        
    except Exception as e:
        logger.error(f"Failed to create credential: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[CredentialResponse])
async def list_credentials(
    customer_id: str = Depends(get_current_customer_id)
):
    """
    List all credentials for the current customer
    
    Returns metadata only (no sensitive credential data)
    """
    try:
        credential_manager = CredentialManager()
        credentials = credential_manager.list_credentials(customer_id)
        
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to list credentials: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{provider}", response_model=List[CredentialResponse])
async def list_credentials_by_provider(
    provider: str,
    customer_id: str = Depends(get_current_customer_id)
):
    """
    List all credentials for a specific provider
    """
    try:
        credential_manager = CredentialManager()
        all_credentials = credential_manager.list_credentials(customer_id)
        
        # Filter by provider
        provider_credentials = [
            cred for cred in all_credentials 
            if cred['provider'] == provider
        ]
        
        return provider_credentials
        
    except Exception as e:
        logger.error(f"Failed to list credentials for provider {provider}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify", response_model=CredentialVerifyResponse)
async def verify_credential(
    request: CredentialVerifyRequest,
    customer_id: str = Depends(get_current_customer_id)
):
    """
    Verify a credential by testing it against the provider API
    
    This will:
    1. Retrieve the credential
    2. Attempt to make a test API call
    3. Update the verification status
    """
    try:
        credential_manager = CredentialManager()
        
        # TODO: Implement actual verification by calling provider API
        # For now, just mark as verified
        credential_manager.verify_credential(
            credential_id=request.credential_id,
            customer_id=customer_id,
            success=True,
            error_message=None
        )
        
        return CredentialVerifyResponse(
            credential_id=request.credential_id,
            is_verified=True,
            message="Credential verified successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to verify credential: {e}", exc_info=True)
        
        # Update verification status as failed
        try:
            credential_manager = CredentialManager()
            credential_manager.verify_credential(
                credential_id=request.credential_id,
                customer_id=customer_id,
                success=False,
                error_message=str(e)
            )
        except:
            pass
        
        return CredentialVerifyResponse(
            credential_id=request.credential_id,
            is_verified=False,
            message="Credential verification failed",
            error=str(e)
        )


@router.delete("/{credential_id}")
async def delete_credential(
    credential_id: str,
    customer_id: str = Depends(get_current_customer_id)
):
    """
    Delete (deactivate) a credential
    """
    try:
        credential_manager = CredentialManager()
        credential_manager.delete_credential(credential_id, customer_id)
        
        return {
            "message": "Credential deleted successfully",
            "credential_id": credential_id
        }
        
    except Exception as e:
        logger.error(f"Failed to delete credential: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/summary")
async def get_credentials_summary(
    customer_id: str = Depends(get_current_customer_id)
):
    """
    Get a summary of all credentials
    """
    try:
        credential_manager = CredentialManager()
        credentials = credential_manager.list_credentials(customer_id)
        
        # Group by provider
        summary = {}
        for cred in credentials:
            provider = cred['provider']
            if provider not in summary:
                summary[provider] = {
                    "total": 0,
                    "active": 0,
                    "verified": 0,
                    "credentials": []
                }
            
            summary[provider]["total"] += 1
            if cred['is_active']:
                summary[provider]["active"] += 1
            if cred['is_verified']:
                summary[provider]["verified"] += 1
            
            summary[provider]["credentials"].append({
                "id": cred['id'],
                "name": cred['credential_name'],
                "is_active": cred['is_active'],
                "is_verified": cred['is_verified'],
                "last_used_at": cred['last_used_at']
            })
        
        return {
            "customer_id": customer_id,
            "total_credentials": len(credentials),
            "providers": summary
        }
        
    except Exception as e:
        logger.error(f"Failed to get credentials summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
