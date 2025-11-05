"""
Analysis API Tests

Tests for analysis API endpoints.
"""

import pytest
from fastapi import status


def test_get_analysis(client):
    """Test analysis endpoint."""
    response = client.get("/analysis/")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "primary_bottleneck" in data
    assert "overall_health" in data
    assert "health_score" in data
    assert "efficiency" in data
    assert "recommendations" in data


def test_get_health_score(client):
    """Test health score endpoint."""
    response = client.get("/analysis/health-score")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "health_score" in data
    assert "overall_health" in data
    assert "primary_bottleneck" in data
    assert 0 <= data["health_score"] <= 100
