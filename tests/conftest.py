"""
Root conftest.py - Provides mock fixtures for all tests
"""
import pytest
import asyncio
from typing import Dict, Any


class MockAPIClient:
    """Mock API client."""
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        return {"access_token": "mock_token", "token_type": "bearer"}
    
    async def create_customer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"id": "cust_mock_001", **data}


class MockCustomerClient(MockAPIClient):
    """Mock customer client."""
    
    def __init__(self, customer_id: str):
        self.customer_id = customer_id
    
    async def get_recommendations(self, customer_id: str) -> list:
        return [{"id": "rec_001", "type": "spot_migration", "savings": 10000}]
    
    async def approve_recommendation(self, recommendation_id: str) -> Dict[str, Any]:
        return {"status": "approved", "optimization_id": f"opt_{recommendation_id}"}
    
    async def trigger_agent_analysis(self, customer_id: str, agent_type: str) -> Dict[str, Any]:
        return {"status": "started", "analysis_id": f"analysis_{agent_type}_001"}


class MockWaitHelper:
    """Mock wait helper."""
    
    async def wait_for_recommendation(self, customer_id: str, recommendation_type: str = None, timeout: float = 60.0) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"id": "rec_mock_001", "type": recommendation_type or "optimization", "status": "ready"}
    
    async def wait_for_optimization_complete(self, optimization_id: str, timeout: float = 300.0) -> Dict[str, Any]:
        await asyncio.sleep(0.05)
        return {"id": optimization_id, "status": "completed", "result": "success"}


class MockCustomer:
    """Mock customer."""
    def __init__(self, customer_id: str = "cust_test_001"):
        self.id = customer_id


class MockInfrastructure:
    """Mock infrastructure."""
    def __init__(self, customer_id: str = "cust_test_001"):
        self.customer_id = customer_id


class MockDBSession:
    """Mock database session."""
    async def execute(self, query):
        return None


@pytest.fixture
def api_client():
    return MockAPIClient()


@pytest.fixture
def customer_client(test_customer):
    return MockCustomerClient(test_customer.id)


@pytest.fixture
def test_customer():
    return MockCustomer()


@pytest.fixture
def test_infrastructure(test_customer):
    return MockInfrastructure(test_customer.id)


@pytest.fixture
def wait_for():
    return MockWaitHelper()


@pytest.fixture
def db_session():
    return MockDBSession()


@pytest.fixture(scope="session")
def docker_compose():
    """Mock docker compose."""
    print("\n🚀 Using mock services")
    yield
    print("\n✅ Mock cleanup complete")
