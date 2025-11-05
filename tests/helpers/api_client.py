"""
API client for E2E tests.
"""
import asyncio
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class OptiInfraClient:
    """High-level API client for testing."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=base_url, timeout=30.0)
        self.token: Optional[str] = None
    
    async def wait_for_health(self, max_retries: int = 30):
        """Wait for API to be healthy."""
        for i in range(max_retries):
            try:
                response = await self.client.get("/health")
                if response.status_code == 200:
                    logger.info(f"✅ API is healthy")
                    return
            except Exception as e:
                logger.debug(f"Health check attempt {i+1}/{max_retries} failed: {e}")
            
            await asyncio.sleep(2)
        
        raise TimeoutError("API did not become healthy in time")
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and store token."""
        response = await self.client.post("/auth/login", json={
            "username": username,
            "password": password
        })
        response.raise_for_status()
        
        data = response.json()
        self.token = data.get("access_token")
        
        # Set authorization header
        if self.token:
            self.client.headers["Authorization"] = f"Bearer {self.token}"
        
        return data
    
    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        response = await self.client.post("/customers", json=data)
        response.raise_for_status()
        return response.json()
    
    async def get_recommendations(self, customer_id: str) -> list:
        """Get recommendations for customer."""
        response = await self.client.get(f"/customers/{customer_id}/recommendations")
        response.raise_for_status()
        return response.json()
    
    async def approve_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """Approve a recommendation."""
        response = await self.client.post(
            f"/recommendations/{recommendation_id}/approve"
        )
        response.raise_for_status()
        return response.json()
    
    async def get_optimization_status(self, optimization_id: str) -> Dict[str, Any]:
        """Get optimization execution status."""
        response = await self.client.get(f"/optimizations/{optimization_id}")
        response.raise_for_status()
        return response.json()
    
    async def get_customer_metrics(
        self, 
        customer_id: str, 
        metric_type: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> list:
        """Get customer metrics."""
        params = {"metric_type": metric_type}
        if start_time:
            params["start_time"] = start_time.isoformat()
        if end_time:
            params["end_time"] = end_time.isoformat()
        
        response = await self.client.get(
            f"/customers/{customer_id}/metrics",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def trigger_agent_analysis(self, customer_id: str, agent_type: str):
        """Manually trigger agent analysis."""
        response = await self.client.post(
            f"/customers/{customer_id}/analyze",
            json={"agent_type": agent_type}
        )
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()


class WebSocketClient:
    """WebSocket client for real-time updates."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.replace("http", "ws")
        self.messages = []
        self.ws = None
    
    async def connect(self, customer_id: str):
        """Connect to WebSocket."""
        try:
            import websockets
            
            self.ws = await websockets.connect(
                f"{self.base_url}/ws/customers/{customer_id}"
            )
        except ImportError:
            logger.warning("websockets package not installed, skipping WebSocket tests")
            raise
    
    async def receive_message(self, timeout: float = 10.0):
        """Receive a message with timeout."""
        if not self.ws:
            return None
        
        try:
            message = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            self.messages.append(message)
            return message
        except asyncio.TimeoutError:
            return None
    
    async def close(self):
        """Close the WebSocket."""
        if self.ws:
            await self.ws.close()
