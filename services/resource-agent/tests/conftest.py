"""
Pytest Configuration

Shared fixtures and configuration for tests.
"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return {
        "agent_id": "resource-agent-test",
        "agent_type": "resource",
        "environment": "test",
        "port": 8003
    }
