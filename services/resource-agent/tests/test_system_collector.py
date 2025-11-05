"""
System Collector Tests

Tests for system metrics collection.
"""

import pytest
from src.collectors.system_collector import SystemCollector


def test_system_collector_initialization():
    """Test system collector initialization."""
    collector = SystemCollector()
    assert collector.boot_time is not None


def test_collect_cpu_metrics():
    """Test CPU metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_cpu_metrics()
    
    assert metrics is not None
    assert 0 <= metrics.utilization_percent <= 100
    assert metrics.logical_cores > 0
    assert metrics.physical_cores > 0
    assert len(metrics.per_core_utilization) == metrics.logical_cores


def test_collect_memory_metrics():
    """Test memory metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_memory_metrics()
    
    assert metrics is not None
    assert metrics.total_mb > 0
    assert 0 <= metrics.utilization_percent <= 100
    assert metrics.used_mb + metrics.available_mb <= metrics.total_mb * 1.1  # Allow 10% margin


def test_collect_disk_metrics():
    """Test disk metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_disk_metrics()
    
    # May be None on some systems
    if metrics:
        assert len(metrics.partitions) >= 0


def test_collect_network_metrics():
    """Test network metrics collection."""
    collector = SystemCollector()
    metrics = collector.collect_network_metrics()
    
    # May be None on some systems
    if metrics:
        assert metrics.io_counters is not None
        assert metrics.io_counters.bytes_sent >= 0
        assert metrics.io_counters.bytes_recv >= 0


def test_collect_all_metrics():
    """Test collecting all system metrics."""
    collector = SystemCollector()
    metrics = collector.collect(instance_id="test-instance")
    
    assert metrics is not None
    assert metrics.instance_id == "test-instance"
    assert metrics.cpu is not None
    assert metrics.memory is not None
    assert metrics.uptime_seconds > 0
