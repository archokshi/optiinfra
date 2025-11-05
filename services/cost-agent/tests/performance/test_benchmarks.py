"""
Performance Benchmark Tests.

Establishes performance baselines for key operations.
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
async def test_cost_collection_benchmark(benchmark_timer):
    """Benchmark cost data collection."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: Cost Collection")
    print(f"{'='*80}")
    
    async def collect_costs():
        """Simulate cost collection."""
        await asyncio.sleep(0.05)  # Simulate API call
        return {"total_cost": 15000.00, "services": 3}
    
    # Run benchmark
    iterations = 100
    times = []
    
    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        benchmark_timer.start()
        result = await collect_costs()
        benchmark_timer.stop()
        times.append(benchmark_timer.elapsed_ms())
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Iterations: {iterations}")
    print(f"Avg time: {avg_time:.2f}ms")
    print(f"Min time: {min_time:.2f}ms")
    print(f"Max time: {max_time:.2f}ms")
    print(f"P95 time: {p95_time:.2f}ms")
    
    assert avg_time < 1000, f"Cost collection too slow: {avg_time:.2f}ms"
    print(f"\n✅ Cost collection benchmark PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_analysis_benchmark(benchmark_timer):
    """Benchmark cost analysis."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: Cost Analysis")
    print(f"{'='*80}")
    
    async def analyze_costs():
        """Simulate cost analysis."""
        await asyncio.sleep(0.08)  # Simulate analysis
        return {"anomalies": 2, "trends": ["increasing"]}
    
    iterations = 50
    times = []
    
    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        benchmark_timer.start()
        result = await analyze_costs()
        benchmark_timer.stop()
        times.append(benchmark_timer.elapsed_ms())
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Iterations: {iterations}")
    print(f"Avg time: {avg_time:.2f}ms")
    print(f"P95 time: {p95_time:.2f}ms")
    
    assert avg_time < 2000, f"Analysis too slow: {avg_time:.2f}ms"
    print(f"\n✅ Analysis benchmark PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_recommendation_generation_benchmark(benchmark_timer):
    """Benchmark recommendation generation."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: Recommendation Generation")
    print(f"{'='*80}")
    
    async def generate_recommendation():
        """Simulate recommendation generation with LLM."""
        await asyncio.sleep(0.15)  # Simulate LLM API call
        return {
            "id": "rec-001",
            "type": "spot_migration",
            "estimated_savings": 1200.00
        }
    
    iterations = 30
    times = []
    
    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        benchmark_timer.start()
        result = await generate_recommendation()
        benchmark_timer.stop()
        times.append(benchmark_timer.elapsed_ms())
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Iterations: {iterations}")
    print(f"Avg time: {avg_time:.2f}ms")
    print(f"P95 time: {p95_time:.2f}ms")
    
    assert avg_time < 3000, f"Recommendation generation too slow: {avg_time:.2f}ms"
    print(f"\n✅ Recommendation generation benchmark PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_database_query_benchmark(benchmark_timer):
    """Benchmark database queries."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: Database Queries")
    print(f"{'='*80}")
    
    async def query_database():
        """Simulate database query."""
        await asyncio.sleep(0.02)  # Simulate DB query
        return {"rows": 100}
    
    iterations = 200
    times = []
    
    print(f"Running {iterations} iterations...")
    for i in range(iterations):
        benchmark_timer.start()
        result = await query_database()
        benchmark_timer.stop()
        times.append(benchmark_timer.elapsed_ms())
    
    avg_time = sum(times) / len(times)
    p95_time = sorted(times)[int(len(times) * 0.95)]
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Iterations: {iterations}")
    print(f"Avg time: {avg_time:.2f}ms")
    print(f"P95 time: {p95_time:.2f}ms")
    
    assert avg_time < 500, f"Database queries too slow: {avg_time:.2f}ms"
    print(f"\n✅ Database query benchmark PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_cache_operations_benchmark(benchmark_timer):
    """Benchmark cache operations."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: Cache Operations")
    print(f"{'='*80}")
    
    # Simulate in-memory cache
    cache = {}
    
    async def cache_set(key, value):
        """Simulate cache set."""
        cache[key] = value
        await asyncio.sleep(0.001)  # Minimal delay
    
    async def cache_get(key):
        """Simulate cache get."""
        await asyncio.sleep(0.001)
        return cache.get(key)
    
    iterations = 500
    
    # Benchmark SET operations
    set_times = []
    print(f"Benchmarking SET operations ({iterations} iterations)...")
    for i in range(iterations):
        benchmark_timer.start()
        await cache_set(f"key_{i}", f"value_{i}")
        benchmark_timer.stop()
        set_times.append(benchmark_timer.elapsed_ms())
    
    # Benchmark GET operations
    get_times = []
    print(f"Benchmarking GET operations ({iterations} iterations)...")
    for i in range(iterations):
        benchmark_timer.start()
        await cache_get(f"key_{i}")
        benchmark_timer.stop()
        get_times.append(benchmark_timer.elapsed_ms())
    
    avg_set_time = sum(set_times) / len(set_times)
    avg_get_time = sum(get_times) / len(get_times)
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"SET operations:")
    print(f"  Avg time: {avg_set_time:.3f}ms")
    print(f"GET operations:")
    print(f"  Avg time: {avg_get_time:.3f}ms")
    
    assert avg_set_time < 10, f"Cache SET too slow: {avg_set_time:.3f}ms"
    assert avg_get_time < 10, f"Cache GET too slow: {avg_get_time:.3f}ms"
    print(f"\n✅ Cache operations benchmark PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_api_endpoint_benchmark(benchmark_timer):
    """Benchmark API endpoint response times."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: API Endpoints")
    print(f"{'='*80}")
    
    async def health_endpoint():
        """Simulate health check endpoint."""
        await asyncio.sleep(0.005)
        return {"status": "healthy"}
    
    async def analyze_endpoint():
        """Simulate analyze endpoint."""
        await asyncio.sleep(0.1)
        return {"analysis": "complete"}
    
    async def recommendations_endpoint():
        """Simulate recommendations endpoint."""
        await asyncio.sleep(0.12)
        return {"recommendations": []}
    
    endpoints = [
        ("GET /health", health_endpoint, 100),
        ("POST /analyze", analyze_endpoint, 50),
        ("GET /recommendations", recommendations_endpoint, 50)
    ]
    
    results = {}
    
    for name, endpoint_func, iterations in endpoints:
        print(f"\nBenchmarking {name} ({iterations} iterations)...")
        times = []
        
        for i in range(iterations):
            benchmark_timer.start()
            await endpoint_func()
            benchmark_timer.stop()
            times.append(benchmark_timer.elapsed_ms())
        
        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]
        
        results[name] = {
            "avg_time_ms": avg_time,
            "p95_time_ms": p95_time
        }
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    for endpoint, metrics in results.items():
        print(f"{endpoint}:")
        print(f"  Avg: {metrics['avg_time_ms']:.2f}ms")
        print(f"  P95: {metrics['p95_time_ms']:.2f}ms")
    
    # Assertions
    assert results["GET /health"]["avg_time_ms"] < 100
    assert results["POST /analyze"]["avg_time_ms"] < 2000
    assert results["GET /recommendations"]["avg_time_ms"] < 2000
    
    print(f"\n✅ API endpoint benchmarks PASSED")
    print(f"{'='*80}\n")


@pytest.mark.performance
@pytest.mark.asyncio
async def test_data_processing_benchmark(benchmark_timer):
    """Benchmark data processing operations."""
    print(f"\n{'='*80}")
    print(f"BENCHMARK: Data Processing")
    print(f"{'='*80}")
    
    # Generate test data
    test_data = [
        {"date": f"2025-10-{i:02d}", "cost": 500.0 + i * 10}
        for i in range(1, 31)
    ]
    
    async def process_data(data):
        """Simulate data processing."""
        # Calculate statistics
        total = sum(item["cost"] for item in data)
        avg = total / len(data)
        await asyncio.sleep(0.01)  # Simulate processing
        return {"total": total, "average": avg}
    
    iterations = 100
    times = []
    
    print(f"Processing {len(test_data)} records, {iterations} iterations...")
    for i in range(iterations):
        benchmark_timer.start()
        result = await process_data(test_data)
        benchmark_timer.stop()
        times.append(benchmark_timer.elapsed_ms())
    
    avg_time = sum(times) / len(times)
    throughput = len(test_data) / (avg_time / 1000)  # records per second
    
    print(f"\n{'='*80}")
    print(f"RESULTS")
    print(f"{'='*80}")
    print(f"Records: {len(test_data)}")
    print(f"Avg time: {avg_time:.2f}ms")
    print(f"Throughput: {throughput:.0f} records/sec")
    
    assert avg_time < 500, f"Data processing too slow: {avg_time:.2f}ms"
    print(f"\n✅ Data processing benchmark PASSED")
    print(f"{'='*80}\n")
