"""
Test Helpers

Utility functions for testing Resource Agent.
"""

from typing import Dict, Any, List
import time
import random


def assert_response_structure(response: Dict[str, Any], required_fields: List[str]):
    """
    Assert that response contains all required fields.
    
    Args:
        response: Response dictionary
        required_fields: List of required field names
    """
    for field in required_fields:
        assert field in response, f"Missing required field: {field}"


def assert_metrics_valid(metrics: Dict[str, Any]):
    """
    Assert that metrics have valid values.
    
    Args:
        metrics: Metrics dictionary
    """
    if "utilization_percent" in metrics:
        assert 0 <= metrics["utilization_percent"] <= 100
    
    if "timestamp" in metrics:
        assert metrics["timestamp"] is not None


def generate_random_metrics() -> Dict[str, Any]:
    """
    Generate random metrics for testing.
    
    Returns:
        Random metrics dictionary
    """
    return {
        "utilization_percent": random.uniform(0, 100),
        "total_mb": random.randint(1000, 100000),
        "used_mb": random.randint(100, 50000),
        "timestamp": time.time()
    }


def wait_for_condition(condition_func, timeout=5, interval=0.1):
    """
    Wait for a condition to become true.
    
    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        
    Returns:
        True if condition met, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition_func():
            return True
        time.sleep(interval)
    return False


def mock_gpu_available():
    """Mock GPU availability check."""
    return False  # Default to no GPU in tests


def mock_lmcache_available():
    """Mock LMCache availability check."""
    return False  # Default to no LMCache in tests
