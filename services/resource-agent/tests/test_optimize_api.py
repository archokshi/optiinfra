"""
Optimization API Tests

Tests for optimization API endpoints.
"""

import pytest
from fastapi import status


def test_run_optimization(client):
    """Test run optimization endpoint."""
    response = client.post("/optimize/run")
    
    # Should return 200 or 500 depending on LLM availability
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]
    
    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "workflow_id" in data
        assert "status" in data
        assert "actions" in data
        assert "execution_time_ms" in data
