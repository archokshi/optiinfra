"""
Real environment fixtures - Connect to actual running services
"""
import pytest
import asyncio
import httpx
from typing import Dict, Any


class RealAPIClient:
    """Real API client for testing with live services."""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.authenticated = False
        self.token = None
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Real login to orchestrator."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                json={"username": username, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.authenticated = True
                return data
            return {"error": "Login failed", "status_code": response.status_code}
        except Exception as e:
            return {"error": str(e)}
    
    async def get(self, endpoint: str) -> Dict[str, Any]:
        """Real GET request."""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            response = await self.client.get(
                f"{self.base_url}{endpoint}",
                headers=headers
            )
            return response.json() if response.status_code == 200 else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    async def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Real POST request."""
        try:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            
            response = await self.client.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=headers
            )
            return response.json() if response.status_code in [200, 201] else {"error": response.text}
        except Exception as e:
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Real health check."""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Real create customer."""
        return await self.post("/api/v1/customers", data)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class RealCustomerClient(RealAPIClient):
    """Real customer-specific API client."""
    
    def __init__(self, customer_id: str, base_url: str = "http://localhost:8080"):
        super().__init__(base_url)
        self.customer_id = customer_id
    
    async def get_recommendations(self, customer_id: str) -> list:
        """Real get recommendations."""
        result = await self.get(f"/api/v1/customers/{customer_id}/recommendations")
        return result.get("recommendations", []) if isinstance(result, dict) else []
    
    async def approve_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        """Real approve recommendation."""
        return await self.post(
            f"/api/v1/recommendations/{recommendation_id}/approve",
            {}
        )
    
    async def trigger_agent_analysis(self, customer_id: str, agent_type: str) -> Dict[str, Any]:
        """Real trigger agent analysis."""
        return await self.post(
            f"/api/v1/customers/{customer_id}/analyze",
            {"agent_type": agent_type}
        )


class RealWaitHelper:
    """Real wait helper for testing."""
    
    def __init__(self, api_client: RealAPIClient):
        self.api_client = api_client
    
    async def wait_for_recommendation(
        self,
        customer_id: str,
        recommendation_type: str = None,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """Wait for recommendation to appear."""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            result = await self.api_client.get(f"/api/v1/customers/{customer_id}/recommendations")
            
            if isinstance(result, dict) and "recommendations" in result:
                recommendations = result["recommendations"]
                if recommendations:
                    if recommendation_type:
                        for rec in recommendations:
                            if rec.get("type") == recommendation_type:
                                return rec
                    else:
                        return recommendations[0]
            
            await asyncio.sleep(2.0)
        
        return {"error": "Timeout waiting for recommendation"}
    
    async def wait_for_optimization_complete(
        self,
        optimization_id: str,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """Wait for optimization to complete."""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            result = await self.api_client.get(f"/api/v1/optimizations/{optimization_id}")
            
            if isinstance(result, dict):
                status = result.get("status")
                if status in ["completed", "failed"]:
                    return result
            
            await asyncio.sleep(5.0)
        
        return {"error": "Timeout waiting for optimization"}


@pytest.fixture
async def real_api_client():
    """Real API client fixture."""
    client = RealAPIClient()
    
    # Check if orchestrator is available
    is_healthy = await client.health_check()
    if not is_healthy:
        pytest.skip("Orchestrator not available at http://localhost:8080")
    
    yield client
    await client.close()


@pytest.fixture
async def real_customer_client(test_customer, real_api_client):
    """Real customer client fixture."""
    client = RealCustomerClient(test_customer.id)
    client.token = real_api_client.token
    yield client
    await client.close()


@pytest.fixture
def real_wait_for(real_api_client):
    """Real wait helper fixture."""
    return RealWaitHelper(real_api_client)
