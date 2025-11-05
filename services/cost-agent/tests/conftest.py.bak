"""
Pytest configuration and fixtures.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """
    Test client for FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def mock_settings(monkeypatch):
    """
    Mock settings for testing.
    """
    monkeypatch.setenv("ORCHESTRATOR_URL", "http://localhost:8080")
    monkeypatch.setenv("AGENT_ID", "test-agent-001")
    monkeypatch.setenv("ENVIRONMENT", "test")


# NEW - Workflow fixtures
@pytest.fixture
def sample_resource_data():
    """
    Sample resource data for testing workflows.
    """
    return {
        "resource_id": "i-test-resource",
        "resource_type": "ec2",
        "provider": "aws",
        "region": "us-east-1",
        "cost_per_month": 150.0,
        "utilization": 0.25,
        "tags": {"environment": "test", "team": "engineering"},
    }
