"""
Test Fixtures

Reusable test data and fixtures for Resource Agent tests.
"""

import pytest
from datetime import datetime
from typing import Dict, Any


# Sample GPU Metrics
SAMPLE_GPU_METRICS = {
    "timestamp": "2025-10-25T19:00:00.000000",
    "instance_id": "test-instance",
    "gpu_count": 2,
    "gpus": [
        {
            "index": 0,
            "name": "NVIDIA A100",
            "uuid": "GPU-12345678",
            "utilization_percent": 85.0,
            "memory_used_mb": 32768,
            "memory_total_mb": 40960,
            "memory_utilization_percent": 80.0,
            "temperature_celsius": 65.0,
            "power_draw_watts": 250.0,
            "power_limit_watts": 300.0
        },
        {
            "index": 1,
            "name": "NVIDIA A100",
            "uuid": "GPU-87654321",
            "utilization_percent": 75.0,
            "memory_used_mb": 28672,
            "memory_total_mb": 40960,
            "memory_utilization_percent": 70.0,
            "temperature_celsius": 62.0,
            "power_draw_watts": 230.0,
            "power_limit_watts": 300.0
        }
    ],
    "total_memory_used_mb": 61440,
    "total_memory_total_mb": 81920,
    "average_gpu_utilization": 80.0,
    "average_memory_utilization": 75.0,
    "average_temperature": 63.5,
    "total_power_draw_watts": 480.0
}


# Sample System Metrics
SAMPLE_SYSTEM_METRICS = {
    "timestamp": "2025-10-25T19:00:00.000000",
    "instance_id": "test-instance",
    "cpu": {
        "utilization_percent": 45.5,
        "cpu_count": 16,
        "physical_cores": 8,
        "cpu_freq_current_mhz": 3200.0,
        "cpu_freq_min_mhz": 800.0,
        "cpu_freq_max_mhz": 4500.0,
        "per_core_utilization": [40.0, 42.0, 45.0, 48.0, 50.0, 43.0, 41.0, 46.0]
    },
    "memory": {
        "total_mb": 32768,
        "available_mb": 16384,
        "used_mb": 16384,
        "utilization_percent": 50.0,
        "swap_total_mb": 8192,
        "swap_used_mb": 1024,
        "swap_utilization_percent": 12.5
    },
    "disk": {
        "total_gb": 1000,
        "used_gb": 600,
        "free_gb": 400,
        "utilization_percent": 60.0,
        "read_bytes_per_sec": 1048576,
        "write_bytes_per_sec": 524288,
        "read_count_per_sec": 100,
        "write_count_per_sec": 50
    },
    "network": {
        "bytes_sent_per_sec": 1048576,
        "bytes_recv_per_sec": 2097152,
        "packets_sent_per_sec": 1000,
        "packets_recv_per_sec": 1500,
        "errors_in": 0,
        "errors_out": 0,
        "drops_in": 0,
        "drops_out": 0
    },
    "boot_time": "2025-10-20T10:00:00.000000",
    "uptime_seconds": 432000
}


# Sample LMCache Metrics
SAMPLE_LMCACHE_METRICS = {
    "status": "enabled",
    "enabled": True,
    "total_size_mb": 2048.0,
    "used_size_mb": 1024.0,
    "available_size_mb": 1024.0,
    "utilization_percent": 50.0,
    "total_requests": 10000,
    "cache_hits": 7500,
    "cache_misses": 2500,
    "hit_rate_percent": 75.0,
    "tokens_cached": 500000,
    "tokens_served": 375000,
    "tokens_computed": 125000,
    "avg_latency_ms": 35.0,
    "cache_hit_latency_ms": 20.0,
    "cache_miss_latency_ms": 80.0,
    "memory_saved_mb": 819.2,
    "memory_savings_percent": 40.0
}


# Sample Analysis Result
SAMPLE_ANALYSIS_RESULT = {
    "timestamp": "2025-10-25T19:00:00.000000",
    "instance_id": "test-instance",
    "primary_bottleneck": "memory",
    "bottlenecks": [
        {
            "type": "memory",
            "severity": "warning",
            "utilization_percent": 85.0,
            "threshold_percent": 85.0,
            "message": "Memory utilization at 85.0%",
            "recommendations": ["Monitor memory usage", "Consider optimization"]
        }
    ],
    "utilization_summary": [
        {
            "resource_type": "cpu",
            "current_percent": 45.5,
            "level": "moderate",
            "is_bottleneck": False
        },
        {
            "resource_type": "memory",
            "current_percent": 85.0,
            "level": "critical",
            "is_bottleneck": True
        }
    ],
    "efficiency": {
        "overall_score": 72.5,
        "cpu_efficiency": 85.0,
        "memory_efficiency": 60.0,
        "cpu_balance_score": 90.0,
        "memory_availability_score": 15.0
    },
    "recommendations": [
        {
            "priority": "warning",
            "category": "memory_optimization",
            "title": "Optimize Memory Usage",
            "description": "Memory utilization is high",
            "expected_impact": "Medium",
            "implementation_effort": "low"
        }
    ],
    "overall_health": "degraded",
    "health_score": 72.5
}


# Sample Workflow Result
SAMPLE_WORKFLOW_RESULT = {
    "workflow_id": "test-workflow-123",
    "status": "completed",
    "timestamp": "2025-10-25T19:00:00.000000",
    "instance_id": "test-instance",
    "primary_bottleneck": "memory",
    "health_score": 72.5,
    "llm_insights": "Memory utilization is high. Consider optimization strategies.",
    "actions": [
        {
            "title": "Optimize Memory Usage",
            "description": "Implement memory optimization strategies",
            "priority": "high",
            "expected_impact": "15% improvement",
            "implementation_effort": "medium",
            "category": "memory_optimization",
            "prerequisites": []
        }
    ],
    "execution_time_ms": 1250.5
}


@pytest.fixture
def sample_gpu_metrics() -> Dict[str, Any]:
    """Fixture for sample GPU metrics."""
    return SAMPLE_GPU_METRICS.copy()


@pytest.fixture
def sample_system_metrics() -> Dict[str, Any]:
    """Fixture for sample system metrics."""
    return SAMPLE_SYSTEM_METRICS.copy()


@pytest.fixture
def sample_lmcache_metrics() -> Dict[str, Any]:
    """Fixture for sample LMCache metrics."""
    return SAMPLE_LMCACHE_METRICS.copy()


@pytest.fixture
def sample_analysis_result() -> Dict[str, Any]:
    """Fixture for sample analysis result."""
    return SAMPLE_ANALYSIS_RESULT.copy()


@pytest.fixture
def sample_workflow_result() -> Dict[str, Any]:
    """Fixture for sample workflow result."""
    return SAMPLE_WORKFLOW_RESULT.copy()
