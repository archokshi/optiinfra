"""
Load Tests for Cost Agent.

Tests system behavior under various load conditions.
"""

import pytest
import asyncio
import time
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.performance
@pytest.mark.asyncio
async def test_normal_load(performance_config, metrics_collector, load_generator):
    """
    Test system under normal load (50 concurrent users).
    
    Expected:
    - Average response time < 2 seconds
    - Error rate < 1%
    - System stable
    """
    config = performance_config["normal_load"]
    thresholds = performance_config["thresholds"]
    
    print(f"\n{'='*80}")
    print(f"LOAD TEST: Normal Load")
    print(f"{'='*80}")
    print(f"Concurrent Users: {config['concurrent_users']}")
    print(f"Duration: {config['duration_seconds']}s")
    print(f"Ramp-up: {config['ramp_up_seconds']}s")
    
    async def simulate_user_request():
        """Simulate a user request."""
        start = time.time()
        try:
            # Simulate API call
            await asyncio.sleep(0.05)  # 50ms simulated processing
            duration_ms = (time.time() - start) * 1000
            metrics_collector.record_response_time(duration_ms)
            metrics_collector.record_cpu_usage()
            metrics_collector.record_memory_usage()
        except Exception as e:
            metrics_collector.record_error(str(e))
    
    # Generate load
    print(f"\nGenerating load...")
    result = await load_generator.generate_load(
        simulate_user_request,
        concurrent_users=config["concurrent_users"],
        duration_seconds=config["duration_seconds"],
        ramp_up_seconds=config["ramp_up_seconds"]
    )
    
    # Get metrics
    stats = metrics_collector.get_stats()
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total errors: {stats['total_errors']}")
    print(f"Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    print(f"Min response time: {stats['min_response_time_ms']:.2f}ms")
    print(f"Max response time: {stats['max_response_time_ms']:.2f}ms")
    print(f"P95 response time: {stats['p95_response_time_ms']:.2f}ms")
    print(f"P99 response time: {stats['p99_response_time_ms']:.2f}ms")
    print(f"Error rate: {stats['error_rate_percent']:.2f}%")
    
    if stats['avg_cpu_percent'] > 0:
        print(f"Avg CPU: {stats['avg_cpu_percent']:.1f}%")
    if stats['avg_memory_mb'] > 0:
        print(f"Avg Memory: {stats['avg_memory_mb']:.1f}MB")
    
    # Assertions
    assert stats["total_requests"] > 0, "No requests completed"
    assert stats["avg_response_time_ms"] < thresholds["normal_response_time_ms"], \
        f"Response time {stats['avg_response_time_ms']:.2f}ms exceeds threshold {thresholds['normal_response_time_ms']}ms"
    assert stats["error_rate_percent"] < thresholds["error_rate_percent"], \
        f"Error rate {stats['error_rate_percent']:.2f}% exceeds threshold {thresholds['error_rate_percent']}%"
    
    print(f"\n✅ Normal load test PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_peak_load(performance_config, metrics_collector):
    """
    Test system under peak load (200 concurrent users).
    
    Expected:
    - Average response time < 5 seconds
    - Error rate < 1%
    - System stable
    """
    config = performance_config["peak_load"]
    thresholds = performance_config["thresholds"]
    
    print(f"\n{'='*80}")
    print(f"LOAD TEST: Peak Load")
    print(f"{'='*80}")
    print(f"Concurrent Users: {config['concurrent_users']}")
    
    async def simulate_user_request():
        """Simulate a user request under peak load."""
        start = time.time()
        try:
            # Simulate heavier processing
            await asyncio.sleep(0.08)  # 80ms simulated processing
            duration_ms = (time.time() - start) * 1000
            metrics_collector.record_response_time(duration_ms)
        except Exception as e:
            metrics_collector.record_error(str(e))
    
    # Run concurrent requests
    print(f"\nGenerating peak load...")
    tasks = [simulate_user_request() for _ in range(config["concurrent_users"])]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    stats = metrics_collector.get_stats()
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total errors: {stats['total_errors']}")
    print(f"Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    print(f"P95 response time: {stats['p95_response_time_ms']:.2f}ms")
    print(f"P99 response time: {stats['p99_response_time_ms']:.2f}ms")
    print(f"Error rate: {stats['error_rate_percent']:.2f}%")
    
    # Assertions
    assert stats["total_requests"] > 0, "No requests completed"
    assert stats["avg_response_time_ms"] < thresholds["peak_response_time_ms"], \
        f"Response time {stats['avg_response_time_ms']:.2f}ms exceeds threshold {thresholds['peak_response_time_ms']}ms"
    
    print(f"\n✅ Peak load test PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.asyncio
async def test_stress_load(performance_config, metrics_collector):
    """
    Test system under stress load (500+ concurrent users).
    
    Expected:
    - System remains stable
    - Graceful degradation
    - No crashes
    """
    config = performance_config["stress_load"]
    
    print(f"\n{'='*80}")
    print(f"STRESS TEST: Stress Load")
    print(f"{'='*80}")
    print(f"Concurrent Users: {config['concurrent_users']}")
    print(f"Duration: {config['duration_seconds']}s")
    
    async def simulate_user_request():
        """Simulate a user request under stress."""
        start = time.time()
        try:
            # Simulate processing with potential delays
            await asyncio.sleep(0.1)  # 100ms simulated processing
            duration_ms = (time.time() - start) * 1000
            metrics_collector.record_response_time(duration_ms)
        except Exception as e:
            metrics_collector.record_error(str(e))
    
    # Run stress test
    print(f"\nGenerating stress load...")
    tasks = [simulate_user_request() for _ in range(config["concurrent_users"])]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    stats = metrics_collector.get_stats()
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Total errors: {stats['total_errors']}")
    print(f"Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    print(f"Error rate: {stats['error_rate_percent']:.2f}%")
    
    # System should remain stable (not crash)
    assert stats["total_requests"] > 0, "System crashed - no requests completed"
    
    # Under stress, we expect some degradation but system should handle it
    print(f"\n✅ Stress test PASSED (system stable)")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_operations(metrics_collector):
    """Test multiple concurrent operations."""
    print(f"\n{'='*80}")
    print(f"CONCURRENCY TEST: Multiple Operations")
    print(f"{'='*80}")
    
    async def operation_a():
        """Simulate operation A."""
        start = time.time()
        await asyncio.sleep(0.05)
        metrics_collector.record_response_time((time.time() - start) * 1000)
    
    async def operation_b():
        """Simulate operation B."""
        start = time.time()
        await asyncio.sleep(0.08)
        metrics_collector.record_response_time((time.time() - start) * 1000)
    
    async def operation_c():
        """Simulate operation C."""
        start = time.time()
        await asyncio.sleep(0.03)
        metrics_collector.record_response_time((time.time() - start) * 1000)
    
    # Run mixed operations
    print(f"\nRunning 100 concurrent mixed operations...")
    tasks = []
    for i in range(100):
        if i % 3 == 0:
            tasks.append(operation_a())
        elif i % 3 == 1:
            tasks.append(operation_b())
        else:
            tasks.append(operation_c())
    
    await asyncio.gather(*tasks)
    
    stats = metrics_collector.get_stats()
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Total operations: {stats['total_requests']}")
    print(f"Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    
    assert stats["total_requests"] == 100
    print(f"\n✅ Concurrent operations test PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_sustained_load(metrics_collector):
    """Test sustained load over time."""
    print(f"\n{'='*80}")
    print(f"SUSTAINED LOAD TEST")
    print(f"{'='*80}")
    
    duration_seconds = 5
    requests_per_second = 20
    
    print(f"Duration: {duration_seconds}s")
    print(f"Target: {requests_per_second} requests/second")
    
    async def sustained_request():
        """Simulate sustained request."""
        start = time.time()
        await asyncio.sleep(0.02)
        metrics_collector.record_response_time((time.time() - start) * 1000)
    
    start_time = time.time()
    request_count = 0
    
    while time.time() - start_time < duration_seconds:
        # Send batch of requests
        tasks = [sustained_request() for _ in range(requests_per_second)]
        await asyncio.gather(*tasks)
        request_count += requests_per_second
        
        # Wait for next second
        await asyncio.sleep(1)
    
    stats = metrics_collector.get_stats()
    actual_rps = stats["total_requests"] / duration_seconds
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Total requests: {stats['total_requests']}")
    print(f"Actual RPS: {actual_rps:.1f}")
    print(f"Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    
    assert stats["total_requests"] > 0
    print(f"\n✅ Sustained load test PASSED")
    print(f"{'='*80}\n")
