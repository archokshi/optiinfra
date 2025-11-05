"""
Vultr API client with authentication, rate limiting, and error handling.
"""

import os
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class VultrAPIError(Exception):
    """Base exception for Vultr API errors"""
    pass


class VultrRateLimitError(VultrAPIError):
    """Raised when rate limit is exceeded"""
    pass


class VultrAuthenticationError(VultrAPIError):
    """Raised when authentication fails"""
    pass


class VultrClient:
    """
    Client for Vultr API v2.
    Handles authentication, rate limiting, and common API operations.
    """
    
    BASE_URL = "https://api.vultr.com/v2"
    
    # Rate limiting: 30 calls per second = 1 call per 33ms
    # We'll be conservative: 500ms per call (default)
    RATE_LIMIT_DELAY = 0.5  # seconds
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        rate_limit_delay: float = RATE_LIMIT_DELAY
    ):
        """
        Initialize Vultr API client.
        
        Args:
            api_key: Vultr API key (or set VULTR_API_KEY env var)
            rate_limit_delay: Delay between API calls in seconds
        """
        self.api_key = api_key or os.getenv("VULTR_API_KEY")
        if not self.api_key:
            raise VultrAuthenticationError(
                "Vultr API key required. Set VULTR_API_KEY environment variable."
            )
        
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
        # Setup session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        logger.info("Vultr client initialized")
    
    def _wait_for_rate_limit(self):
        """Wait to respect rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, VultrRateLimitError)),
        reraise=True
    )
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request with rate limiting and retries.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body data
        
        Returns:
            Response JSON data
        
        Raises:
            VultrAPIError: On API errors
            VultrRateLimitError: On rate limit exceeded
            VultrAuthenticationError: On authentication failure
        """
        self._wait_for_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("Rate limit exceeded, will retry")
                raise VultrRateLimitError("Rate limit exceeded")
            
            # Handle authentication errors
            if response.status_code == 401:
                raise VultrAuthenticationError("Invalid API key")
            
            # Handle other errors
            if response.status_code >= 400:
                error_msg = response.json().get("error", response.text)
                raise VultrAPIError(
                    f"API error {response.status_code}: {error_msg}"
                )
            
            return response.json()
            
        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request"""
        return self._request("GET", endpoint, params=params)
    
    def post(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a POST request"""
        return self._request("POST", endpoint, data=data)
    
    def get_paginated(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        per_page: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all pages of results from a paginated endpoint.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            per_page: Items per page (max 500)
        
        Returns:
            List of all items across all pages
        """
        all_items = []
        params = params or {}
        params["per_page"] = min(per_page, 500)  # Vultr max is 500
        
        cursor = None
        
        while True:
            if cursor:
                params["cursor"] = cursor
            
            response = self.get(endpoint, params=params)
            
            # Extract items (key varies by endpoint)
            # Common keys: instances, invoices, bare_metals, etc.
            items = None
            for key in response.keys():
                if isinstance(response[key], list):
                    items = response[key]
                    break
            
            if items:
                all_items.extend(items)
            
            # Check for next page
            meta = response.get("meta", {})
            links = meta.get("links", {})
            cursor = links.get("next")
            
            if not cursor:
                break
            
            logger.debug(f"Fetching next page: {cursor}")
        
        logger.info(f"Retrieved {len(all_items)} items from {endpoint}")
        return all_items
    
    # ============================================================
    # CONVENIENCE METHODS
    # ============================================================
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balance"""
        return self.get("/account")
    
    def list_invoices(self) -> List[Dict[str, Any]]:
        """List all invoices"""
        return self.get_paginated("/billing/invoices")
    
    def get_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """Get specific invoice details"""
        return self.get(f"/billing/invoices/{invoice_id}")
    
    def get_invoice_items(self, invoice_id: str) -> List[Dict[str, Any]]:
        """Get line items for an invoice"""
        response = self.get(f"/billing/invoices/{invoice_id}/items")
        return response.get("invoice_items", [])
    
    def get_pending_charges(self) -> Dict[str, Any]:
        """Get current month's pending charges"""
        return self.get("/billing/pending-charges")
    
    def get_billing_history(self) -> Dict[str, Any]:
        """Get billing history"""
        return self.get("/billing/history")
    
    def list_instances(self) -> List[Dict[str, Any]]:
        """List all Cloud Compute instances"""
        return self.get_paginated("/instances")
    
    def list_bare_metals(self) -> List[Dict[str, Any]]:
        """List all Bare Metal servers"""
        return self.get_paginated("/bare-metals")
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """List all available plans"""
        return self.get_paginated("/plans")


# Async version for async contexts
class AsyncVultrClient(VultrClient):
    """
    Async version of Vultr client using aiohttp.
    Use this in async/await contexts.
    """
    
    def __init__(self, *args, **kwargs):
        import aiohttp
        super().__init__(*args, **kwargs)
        self.async_session = None
    
    async def __aenter__(self):
        import aiohttp
        self.async_session = aiohttp.ClientSession(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.async_session:
            await self.async_session.close()
    
    async def _async_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Async version of _request"""
        import aiohttp
        
        self._wait_for_rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        async with self.async_session.request(
            method=method,
            url=url,
            params=params,
            json=data,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            
            if response.status == 429:
                raise VultrRateLimitError("Rate limit exceeded")
            
            if response.status == 401:
                raise VultrAuthenticationError("Invalid API key")
            
            if response.status >= 400:
                error_text = await response.text()
                raise VultrAPIError(f"API error {response.status}: {error_text}")
            
            return await response.json()
    
    async def get_async(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Async GET request"""
        return await self._async_request("GET", endpoint, params=params)
