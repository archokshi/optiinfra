"""
Test Configuration

Shared fixtures for tests.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_orchestrator_url():
    """Mock orchestrator URL."""
    return "http://mock-orchestrator:8080"
