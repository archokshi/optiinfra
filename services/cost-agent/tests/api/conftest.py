"""
API Test Fixtures.

Shared fixtures for API testing.
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import app
from src.auth.api_key import APIKeyManager


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
async def test_api_key():
    """Create test API key."""
    plain_key, key_record = await APIKeyManager.create_key(
        customer_id="cust-test",
        name="Test API Key",
        expires_days=1
    )
    return plain_key


@pytest.fixture
def auth_headers(test_api_key):
    """Create authentication headers."""
    return {"X-API-Key": test_api_key}


@pytest.fixture
def test_customer_id():
    """Test customer ID."""
    return "cust-test"
