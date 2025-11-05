"""
GPU API Tests

Tests for GPU metrics API endpoints.
"""

import pytest
from fastapi import status
from unittest.mock import patch, Mock


def test_get_gpu_info(client):
    """Test GPU info endpoint."""
    response = client.get("/gpu/info")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "available" in data
    assert "gpu_count" in data


@pytest.mark.skipif(True, reason="Requires GPU hardware")
def test_get_gpu_metrics(client):
    """Test GPU metrics endpoint."""
    response = client.get("/gpu/metrics")
    
    # Will return 503 if no GPU available
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE]


@pytest.mark.skipif(True, reason="Requires GPU hardware")
def test_get_single_gpu_metrics(client):
    """Test single GPU metrics endpoint."""
    response = client.get("/gpu/metrics/0")
    
    # Will return 503 if no GPU available, 404 if GPU not found
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_404_NOT_FOUND,
        status.HTTP_503_SERVICE_UNAVAILABLE
    ]
