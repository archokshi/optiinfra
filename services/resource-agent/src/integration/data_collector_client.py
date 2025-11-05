"""
Data Collector Client - Integration with data-collector service
Phase 6.3: Cost Agent Refactor

Allows cost-agent to trigger data collection and check status
"""
import os
import logging
import httpx
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DataCollectorClient:
    """
    Client for interacting with the data-collector service
    
    Provides methods to:
    - Trigger data collection
    - Check collection status
    - View collection history
    """
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the data collector client
        
        Args:
            base_url: Base URL of the data-collector service
                     (default: from environment or http://localhost:8005)
        """
        self.base_url = base_url or os.getenv("DATA_COLLECTOR_URL", "http://data-collector:8005")
        self.timeout = 30.0
        logger.info(f"DataCollectorClient initialized with base_url: {self.base_url}")
    
    def trigger_collection(
        self,
        customer_id: str,
        provider: str,
        data_types: Optional[List[str]] = None,
        async_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Trigger data collection for a customer and provider
        
        Args:
            customer_id: Customer UUID
            provider: Cloud provider (vultr, aws, gcp, azure)
            data_types: List of data types to collect (default: ["cost"])
            async_mode: Whether to run collection asynchronously (default: True)
        
        Returns:
            Dict with task_id and status
        """
        if data_types is None:
            data_types = ["cost"]
        
        url = f"{self.base_url}/api/v1/collect/trigger"
        payload = {
            "customer_id": customer_id,
            "provider": provider,
            "data_types": data_types,
            "async_mode": async_mode
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Collection triggered for {customer_id}/{provider}: {result.get('task_id')}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error triggering collection: {e.response.status_code} - {e.response.text}")
            return {
                "error": f"HTTP {e.response.status_code}",
                "message": e.response.text
            }
        except Exception as e:
            logger.error(f"Failed to trigger collection: {e}", exc_info=True)
            return {
                "error": "ConnectionError",
                "message": str(e)
            }
    
    def get_collection_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a collection task
        
        Args:
            task_id: Task ID returned from trigger_collection
        
        Returns:
            Dict with task status and details
        """
        url = f"{self.base_url}/api/v1/collect/status/{task_id}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Collection status for {task_id}: {result.get('status')}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting collection status: {e.response.status_code}")
            return {
                "error": f"HTTP {e.response.status_code}",
                "message": e.response.text
            }
        except Exception as e:
            logger.error(f"Failed to get collection status: {e}", exc_info=True)
            return {
                "error": "ConnectionError",
                "message": str(e)
            }
    
    def get_collection_history(
        self,
        customer_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get collection history for a customer
        
        Args:
            customer_id: Customer UUID
            limit: Maximum number of records to return
        
        Returns:
            List of collection history records
        """
        url = f"{self.base_url}/api/v1/collect/history"
        params = {
            "customer_id": customer_id,
            "limit": limit
        }
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Retrieved {len(result)} collection history records for {customer_id}")
                return result
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error getting collection history: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Failed to get collection history: {e}", exc_info=True)
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if the data-collector service is healthy
        
        Returns:
            Dict with health status
        """
        url = f"{self.base_url}/health"
        
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Data-collector health: {result.get('status')}")
                return result
                
        except Exception as e:
            logger.error(f"Data-collector health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def get_collectors_status(self) -> Dict[str, Any]:
        """
        Get status of all collectors
        
        Returns:
            Dict with collector status information
        """
        url = f"{self.base_url}/api/v1/collectors/status"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url)
                response.raise_for_status()
                result = response.json()
                
                logger.info("Retrieved collectors status")
                return result
                
        except Exception as e:
            logger.error(f"Failed to get collectors status: {e}", exc_info=True)
            return {
                "error": str(e)
            }
