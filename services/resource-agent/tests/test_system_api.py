"""
System API Tests

Tests for system metrics API endpoints.
"""

import pytest
from fastapi import status


def test_get_system_metrics(client):
    """Test system metrics endpoint."""
    response = client.get("/system/metrics")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
    assert "instance_id" in data


def test_get_cpu_metrics(client):
    """Test CPU metrics endpoint."""
    response = client.get("/system/metrics/cpu")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "utilization_percent" in data
    assert "logical_cores" in data


def test_get_memory_metrics(client):
    """Test memory metrics endpoint."""
    response = client.get("/system/metrics/memory")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_mb" in data
    assert "utilization_percent" in data


def test_get_disk_metrics(client):
    """Test disk metrics endpoint."""
    response = client.get("/system/metrics/disk")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "partitions" in data


def test_get_network_metrics(client):
    """Test network metrics endpoint."""
    response = client.get("/system/metrics/network")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "io_counters" in data
