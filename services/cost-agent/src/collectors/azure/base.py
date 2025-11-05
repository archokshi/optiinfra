"""
Azure Base Collector

Provides common functionality for all Azure collectors including:
- Credential management (Service Principal, Managed Identity, CLI)
- Rate limiting and throttling
- Error handling and retry logic
- Resource ID parsing
- Logging
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.exceptions import AzureError, HttpResponseError, ResourceNotFoundError
from azure.mgmt.resource import ResourceManagementClient
import time


class AzureBaseCollector:
    """Base class for Azure resource collectors with common functionality"""
    
    def __init__(
        self,
        subscription_id: str,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize base collector
        
        Args:
            subscription_id: Azure subscription ID
            tenant_id: Azure AD tenant ID (optional, for Service Principal)
            client_id: Service Principal client ID (optional)
            client_secret: Service Principal client secret (optional)
        """
        self.subscription_id = subscription_id
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        
        # Initialize credentials
        self.credentials = self._get_credentials()
        
        # Rate limiting (100 requests/minute per subscription)
        self.rate_limit_calls = 100
        self.rate_limit_period = 60  # seconds
        self.api_calls = []
        
        # Retry configuration
        self.retry_config = {
            "max_attempts": 3,
            "backoff_factor": 2,
            "initial_delay": 1
        }
        
        # Logging
        self.logger = logging.getLogger(__name__)
    
    def _get_credentials(self):
        """
        Get Azure credentials
        
        Returns:
            Azure credentials object
        """
        if self.client_id and self.client_secret and self.tenant_id:
            # Use Service Principal
            self.logger.info("Using Service Principal authentication")
            return ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        else:
            # Use DefaultAzureCredential (Managed Identity, CLI, etc.)
            self.logger.info("Using DefaultAzureCredential authentication")
            return DefaultAzureCredential()
    
    async def _rate_limit(self):
        """
        Implement rate limiting
        
        Ensures we don't exceed 100 requests/minute per subscription
        """
        now = time.time()
        
        # Remove old API calls outside the time window
        self.api_calls = [call_time for call_time in self.api_calls 
                         if now - call_time < self.rate_limit_period]
        
        # Check if we've hit the limit
        if len(self.api_calls) >= self.rate_limit_calls:
            # Calculate wait time
            oldest_call = min(self.api_calls)
            wait_time = self.rate_limit_period - (now - oldest_call)
            
            if wait_time > 0:
                self.logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        # Record this API call
        self.api_calls.append(now)
    
    async def _make_request(
        self,
        client: Any,
        method: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Make rate-limited API request with retry logic
        
        Args:
            client: Azure SDK client
            method: Method name to call
            *args, **kwargs: Method arguments
            
        Returns:
            API response
            
        Raises:
            AzureError: If request fails after retries
        """
        for attempt in range(self.retry_config["max_attempts"]):
            try:
                # Apply rate limiting
                await self._rate_limit()
                
                # Make the request
                method_func = getattr(client, method)
                result = method_func(*args, **kwargs)
                
                # Log successful call
                self.logger.debug(f"API call successful: {method}")
                return result
                
            except HttpResponseError as e:
                if e.status_code == 429:  # Rate limit
                    delay = self.retry_config["backoff_factor"] ** attempt
                    self.logger.warning(f"Rate limited (429), retrying in {delay}s")
                    await asyncio.sleep(delay)
                elif e.status_code >= 500:  # Server error
                    delay = self.retry_config["backoff_factor"] ** attempt
                    self.logger.warning(f"Server error ({e.status_code}), retrying in {delay}s")
                    await asyncio.sleep(delay)
                else:
                    # Client error, don't retry
                    self.logger.error(f"Client error ({e.status_code}): {str(e)}")
                    raise
                    
            except ResourceNotFoundError as e:
                self.logger.error(f"Resource not found: {str(e)}")
                raise
                
            except AzureError as e:
                if attempt == self.retry_config["max_attempts"] - 1:
                    self.logger.error(f"Azure error after {attempt + 1} attempts: {str(e)}")
                    raise
                delay = self.retry_config["initial_delay"]
                self.logger.warning(f"Azure error, retrying in {delay}s: {str(e)}")
                await asyncio.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"Unexpected error: {str(e)}")
                if attempt == self.retry_config["max_attempts"] - 1:
                    raise
                await asyncio.sleep(self.retry_config["initial_delay"])
        
        raise AzureError("Max retries exceeded")
    
    async def _handle_pagination(self, paged_result):
        """
        Handle paginated Azure API responses
        
        Args:
            paged_result: Azure paged result iterator
            
        Returns:
            List of all results
        """
        results = []
        try:
            for item in paged_result:
                results.append(item)
        except Exception as e:
            self.logger.error(f"Pagination error: {str(e)}")
            raise
        return results
    
    def _handle_error(self, error: Exception) -> Dict:
        """
        Standardized error handling
        
        Args:
            error: Exception to handle
            
        Returns:
            Error dictionary
        """
        error_dict = {
            "error": True,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if isinstance(error, HttpResponseError):
            error_dict["status_code"] = error.status_code
            error_dict["error_code"] = error.error.code if hasattr(error, 'error') else None
        
        self.logger.error(f"Error occurred: {error_dict}")
        return error_dict
    
    def _parse_resource_id(self, resource_id: str) -> Dict:
        """
        Parse Azure resource ID into components
        
        Args:
            resource_id: Azure resource ID (e.g., /subscriptions/{sub}/resourceGroups/{rg}/...)
            
        Returns:
            Dictionary with subscription_id, resource_group, provider, resource_type, name
        """
        parts = resource_id.split('/')
        
        parsed = {
            "subscription_id": None,
            "resource_group": None,
            "provider": None,
            "resource_type": None,
            "name": None
        }
        
        try:
            for i, part in enumerate(parts):
                if part.lower() == 'subscriptions' and i + 1 < len(parts):
                    parsed["subscription_id"] = parts[i + 1]
                elif part.lower() == 'resourcegroups' and i + 1 < len(parts):
                    parsed["resource_group"] = parts[i + 1]
                elif part.lower() == 'providers' and i + 1 < len(parts):
                    parsed["provider"] = parts[i + 1]
                    if i + 2 < len(parts):
                        parsed["resource_type"] = parts[i + 2]
                    if i + 3 < len(parts):
                        parsed["name"] = parts[i + 3]
        except Exception as e:
            self.logger.warning(f"Failed to parse resource ID {resource_id}: {str(e)}")
        
        return parsed
    
    def _get_resource_group_from_id(self, resource_id: str) -> Optional[str]:
        """
        Extract resource group name from resource ID
        
        Args:
            resource_id: Azure resource ID
            
        Returns:
            Resource group name or None
        """
        parsed = self._parse_resource_id(resource_id)
        return parsed.get("resource_group")
    
    def _get_resource_name_from_id(self, resource_id: str) -> Optional[str]:
        """
        Extract resource name from resource ID
        
        Args:
            resource_id: Azure resource ID
            
        Returns:
            Resource name or None
        """
        parsed = self._parse_resource_id(resource_id)
        return parsed.get("name")
