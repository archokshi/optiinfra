# PHASE1-1.14b PART1: Performance Tests - Code Implementation

**Phase:** Cost Agent - Week 2  
**Objective:** Create comprehensive performance and load tests  
**Priority:** MEDIUM  
**Estimated Effort:** 25 minutes (code) + 20 minutes (execution)  
**Date:** October 23, 2025

---

## 📋 OVERVIEW

PHASE1-1.14b focuses on **creating comprehensive performance and load tests** to validate the Cost Agent's performance under various load conditions. This includes load testing, stress testing, and performance benchmarking.

### What We're Testing
1. **Load Testing** - System behavior under expected load
2. **Stress Testing** - System behavior under extreme load
3. **Performance Benchmarks** - Response time and throughput metrics
4. **Scalability Testing** - System scaling characteristics
5. **Resource Usage** - CPU, memory, database connections
6. **Concurrent Operations** - Multiple simultaneous operations

**Key Differences from PHASE1-1.14:**
- **PHASE1-1.14:** E2E workflow tests (functional)
- **PHASE1-1.14b:** Performance and load tests (non-functional)

**Expected Impact:** Confidence in production performance, validated scalability

---

## 🎯 OBJECTIVES

### Primary Goals
1. **Load Testing:**
   - Test under normal load (10-50 concurrent users)
   - Test under peak load (100-200 concurrent users)
   - Test under stress load (500+ concurrent users)
   - Measure response times and throughput

2. **Performance Benchmarks:**
   - API endpoint response times
   - Data collection performance
   - Analysis engine performance
   - Recommendation generation performance
   - Database query performance

3. **Resource Monitoring:**
   - CPU utilization
   - Memory usage
   - Database connections
   - Network I/O
   - Disk I/O

4. **Scalability Testing:**
   - Horizontal scaling validation
   - Database connection pooling
   - Cache effectiveness
   - Queue processing

### Success Criteria
- ✅ 15+ performance tests
- ✅ All tests passing
- ✅ < 2 seconds average response time under normal load
- ✅ < 5 seconds average response time under peak load
- ✅ System stable under stress load
- ✅ Resource usage within acceptable limits

---

## 🏗️ TEST ARCHITECTURE

### Performance Test Organization

```
tests/
├── performance/                        # Performance tests
│   ├── __init__.py
│   ├── conftest.py                     # Performance fixtures
│   ├── test_load.py                    # Load tests
│   ├── test_stress.py                  # Stress tests
│   ├── test_benchmarks.py              # Performance benchmarks
│   ├── test_scalability.py             # Scalability tests
│   └── test_resource_usage.py          # Resource monitoring
├── fixtures/
│   └── performance_data.py             # Performance test data
└── utils/
    ├── load_generator.py               # Load generation utilities
    └── metrics_collector.py            # Metrics collection
```

---

## 📦 IMPLEMENTATION PHASES

### Phase 1: Performance Test Infrastructure (5 min)

**Objective:** Set up performance testing infrastructure

**Tasks:**
1. Create performance test directory
2. Set up performance fixtures
3. Create load generation utilities
4. Set up metrics collection
5. Configure performance test markers

**Files to Create:**
- `tests/performance/__init__.py`
- `tests/performance/conftest.py`
- `tests/utils/load_generator.py`
- `tests/utils/metrics_collector.py`

**Dependencies:**
```bash
pip install pytest-benchmark pytest-asyncio locust
```

---

### Phase 2: Load Tests (10 min)

**Objective:** Test system under various load conditions

**Scenarios to Test:**
1. **Normal Load (10-50 concurrent users)**
   - Cost collection requests
   - Analysis requests
   - Recommendation requests
   - Average response time < 2s

2. **Peak Load (100-200 concurrent users)**
   - All API endpoints
   - Database queries
   - Cache operations
   - Average response time < 5s

3. **Stress Load (500+ concurrent users)**
   - System stability
   - Error rates
   - Resource exhaustion
   - Graceful degradation

**Files to Create:**
- `tests/performance/test_load.py`

---

### Phase 3: Performance Benchmarks (5 min)

**Objective:** Establish performance baselines

**Benchmarks to Create:**
1. **API Endpoint Benchmarks**
   - GET /health
   - POST /analyze
   - POST /recommendations
   - GET /recommendations/{id}

2. **Component Benchmarks**
   - Cost data collection
   - Anomaly detection
   - Recommendation generation
   - LLM API calls

3. **Database Benchmarks**
   - Query performance
   - Insert performance
   - Update performance
   - Connection pooling

**Files to Create:**
- `tests/performance/test_benchmarks.py`

---

### Phase 4: Scalability Tests (3 min)

**Objective:** Validate system scalability

**Tests:**
1. **Horizontal Scaling**
   - Multiple worker processes
   - Load distribution
   - State synchronization

2. **Database Scaling**
   - Connection pool sizing
   - Query optimization
   - Index effectiveness

3. **Cache Scaling**
   - Cache hit rates
   - Cache invalidation
   - Memory usage

**Files to Create:**
- `tests/performance/test_scalability.py`

---

### Phase 5: Resource Usage Tests (2 min)

**Objective:** Monitor resource consumption

**Metrics to Track:**
1. **CPU Usage**
   - Average CPU utilization
   - Peak CPU utilization
   - CPU per request

2. **Memory Usage**
   - Average memory usage
   - Peak memory usage
   - Memory leaks

3. **Database Connections**
   - Active connections
   - Connection pool usage
   - Connection leaks

**Files to Create:**
- `tests/performance/test_resource_usage.py`

---

## 📋 DETAILED IMPLEMENTATION

### Phase 1: Performance Test Infrastructure

#### Step 1.1: Performance Test Configuration

**File:** `tests/performance/conftest.py`

```python
"""
Performance Test Configuration and Fixtures.
"""

import pytest
import asyncio
import time
from typing import Dict, List
from datetime import datetime
import psutil
import os


@pytest.fixture(scope="session")
def performance_config():
    """Performance test configuration."""
    return {
        "normal_load": {
            "concurrent_users": 50,
            "duration_seconds": 30,
            "ramp_up_seconds": 5
        },
        "peak_load": {
            "concurrent_users": 200,
            "duration_seconds": 60,
            "ramp_up_seconds": 10
        },
        "stress_load": {
            "concurrent_users": 500,
            "duration_seconds": 120,
            "ramp_up_seconds": 20
        },
        "thresholds": {
            "normal_response_time_ms": 2000,
            "peak_response_time_ms": 5000,
            "error_rate_percent": 1.0,
            "cpu_percent": 80,
            "memory_mb": 512
        }
    }


@pytest.fixture
def metrics_collector():
    """Metrics collection fixture."""
    class MetricsCollector:
        def __init__(self):
            self.metrics = {
                "response_times": [],
                "errors": [],
                "cpu_usage": [],
                "memory_usage": []
            }
        
        def record_response_time(self, duration_ms: float):
            self.metrics["response_times"].append(duration_ms)
        
        def record_error(self, error: str):
            self.metrics["errors"].append(error)
        
        def record_cpu_usage(self):
            self.metrics["cpu_usage"].append(psutil.cpu_percent())
        
        def record_memory_usage(self):
            process = psutil.Process(os.getpid())
            self.metrics["memory_usage"].append(process.memory_info().rss / 1024 / 1024)
        
        def get_stats(self) -> Dict:
            response_times = self.metrics["response_times"]
            return {
                "total_requests": len(response_times),
                "total_errors": len(self.metrics["errors"]),
                "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
                "min_response_time_ms": min(response_times) if response_times else 0,
                "max_response_time_ms": max(response_times) if response_times else 0,
                "p95_response_time_ms": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
                "p99_response_time_ms": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
                "error_rate_percent": (len(self.metrics["errors"]) / len(response_times) * 100) if response_times else 0,
                "avg_cpu_percent": sum(self.metrics["cpu_usage"]) / len(self.metrics["cpu_usage"]) if self.metrics["cpu_usage"] else 0,
                "avg_memory_mb": sum(self.metrics["memory_usage"]) / len(self.metrics["memory_usage"]) if self.metrics["memory_usage"] else 0
            }
    
    return MetricsCollector()


@pytest.fixture
async def load_generator():
    """Load generation fixture."""
    class LoadGenerator:
        async def generate_load(
            self,
            target_function,
            concurrent_users: int,
            duration_seconds: int,
            ramp_up_seconds: int = 0
        ):
            """Generate load by running target function concurrently."""
            start_time = time.time()
            tasks = []
            
            # Ramp up
            if ramp_up_seconds > 0:
                users_per_second = concurrent_users / ramp_up_seconds
                for i in range(concurrent_users):
                    if i > 0 and i % users_per_second == 0:
                        await asyncio.sleep(1)
                    tasks.append(asyncio.create_task(target_function()))
            else:
                tasks = [asyncio.create_task(target_function()) for _ in range(concurrent_users)]
            
            # Wait for duration
            await asyncio.sleep(duration_seconds)
            
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            return {
                "duration": time.time() - start_time,
                "tasks_completed": sum(1 for t in tasks if t.done() and not t.cancelled())
            }
    
    return LoadGenerator()
```

#### Step 1.2: Load Generator Utility

**File:** `tests/utils/load_generator.py`

```python
"""
Load Generation Utilities.
"""

import asyncio
import time
from typing import Callable, Dict, List
from datetime import datetime


class LoadGenerator:
    """Generate load for performance testing."""
    
    def __init__(self):
        self.results = []
    
    async def run_concurrent_requests(
        self,
        request_func: Callable,
        num_requests: int,
        concurrent_limit: int = 10
    ) -> Dict:
        """
        Run concurrent requests with a concurrency limit.
        
        Args:
            request_func: Async function to call
            num_requests: Total number of requests
            concurrent_limit: Maximum concurrent requests
            
        Returns:
            Performance metrics
        """
        semaphore = asyncio.Semaphore(concurrent_limit)
        results = []
        
        async def limited_request():
            async with semaphore:
                start = time.time()
                try:
                    await request_func()
                    duration = (time.time() - start) * 1000  # ms
                    results.append({"success": True, "duration_ms": duration})
                except Exception as e:
                    duration = (time.time() - start) * 1000
                    results.append({"success": False, "duration_ms": duration, "error": str(e)})
        
        start_time = time.time()
        await asyncio.gather(*[limited_request() for _ in range(num_requests)])
        total_duration = time.time() - start_time
        
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]
        
        durations = [r["duration_ms"] for r in successful]
        
        return {
            "total_requests": num_requests,
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "total_duration_seconds": total_duration,
            "requests_per_second": num_requests / total_duration,
            "avg_response_time_ms": sum(durations) / len(durations) if durations else 0,
            "min_response_time_ms": min(durations) if durations else 0,
            "max_response_time_ms": max(durations) if durations else 0,
            "p95_response_time_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "p99_response_time_ms": sorted(durations)[int(len(durations) * 0.99)] if durations else 0
        }
    
    async def ramp_up_load(
        self,
        request_func: Callable,
        start_users: int,
        end_users: int,
        ramp_duration_seconds: int
    ) -> List[Dict]:
        """
        Gradually increase load from start_users to end_users.
        
        Args:
            request_func: Async function to call
            start_users: Starting number of concurrent users
            end_users: Ending number of concurrent users
            ramp_duration_seconds: Duration of ramp-up
            
        Returns:
            List of metrics at each step
        """
        steps = 10
        step_duration = ramp_duration_seconds / steps
        user_increment = (end_users - start_users) / steps
        
        metrics = []
        
        for step in range(steps):
            current_users = int(start_users + (user_increment * step))
            print(f"  Ramp-up step {step + 1}/{steps}: {current_users} users")
            
            result = await self.run_concurrent_requests(
                request_func,
                num_requests=current_users * 10,  # 10 requests per user
                concurrent_limit=current_users
            )
            
            metrics.append({
                "step": step + 1,
                "concurrent_users": current_users,
                **result
            })
            
            await asyncio.sleep(step_duration)
        
        return metrics
```

---

### Phase 2: Load Tests

#### Step 2.1: Load Test Implementation

**File:** `tests/performance/test_load.py`

```python
"""
Load Tests for Cost Agent.

Tests system behavior under various load conditions.
"""

import pytest
import asyncio
import time
from datetime import datetime


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
    
    print(f"\n[LOAD TEST] Normal Load: {config['concurrent_users']} concurrent users")
    print(f"Duration: {config['duration_seconds']}s, Ramp-up: {config['ramp_up_seconds']}s")
    
    async def simulate_user_request():
        """Simulate a user request."""
        start = time.time()
        await asyncio.sleep(0.1)  # Simulate API call
        duration_ms = (time.time() - start) * 1000
        metrics_collector.record_response_time(duration_ms)
        metrics_collector.record_cpu_usage()
        metrics_collector.record_memory_usage()
    
    # Generate load
    result = await load_generator.generate_load(
        simulate_user_request,
        concurrent_users=config["concurrent_users"],
        duration_seconds=config["duration_seconds"],
        ramp_up_seconds=config["ramp_up_seconds"]
    )
    
    # Get metrics
    stats = metrics_collector.get_stats()
    
    print(f"\n[RESULTS]")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    print(f"  P95 response time: {stats['p95_response_time_ms']:.2f}ms")
    print(f"  P99 response time: {stats['p99_response_time_ms']:.2f}ms")
    print(f"  Error rate: {stats['error_rate_percent']:.2f}%")
    print(f"  Avg CPU: {stats['avg_cpu_percent']:.1f}%")
    print(f"  Avg Memory: {stats['avg_memory_mb']:.1f}MB")
    
    # Assertions
    assert stats["avg_response_time_ms"] < thresholds["normal_response_time_ms"]
    assert stats["error_rate_percent"] < thresholds["error_rate_percent"]
    print("\n✅ Normal load test PASSED")


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
    
    print(f"\n[LOAD TEST] Peak Load: {config['concurrent_users']} concurrent users")
    
    async def simulate_user_request():
        start = time.time()
        await asyncio.sleep(0.15)  # Simulate heavier load
        duration_ms = (time.time() - start) * 1000
        metrics_collector.record_response_time(duration_ms)
    
    # Run concurrent requests
    tasks = [simulate_user_request() for _ in range(config["concurrent_users"])]
    await asyncio.gather(*tasks)
    
    stats = metrics_collector.get_stats()
    
    print(f"\n[RESULTS]")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Avg response time: {stats['avg_response_time_ms']:.2f}ms")
    print(f"  P95 response time: {stats['p95_response_time_ms']:.2f}ms")
    
    assert stats["avg_response_time_ms"] < thresholds["peak_response_time_ms"]
    print("\n✅ Peak load test PASSED")


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
    
    print(f"\n[STRESS TEST] Stress Load: {config['concurrent_users']} concurrent users")
    
    async def simulate_user_request():
        start = time.time()
        try:
            await asyncio.sleep(0.2)
            duration_ms = (time.time() - start) * 1000
            metrics_collector.record_response_time(duration_ms)
        except Exception as e:
            metrics_collector.record_error(str(e))
    
    # Run stress test
    tasks = [simulate_user_request() for _ in range(config["concurrent_users"])]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    stats = metrics_collector.get_stats()
    
    print(f"\n[RESULTS]")
    print(f"  Total requests: {stats['total_requests']}")
    print(f"  Total errors: {stats['total_errors']}")
    print(f"  Error rate: {stats['error_rate_percent']:.2f}%")
    
    # System should remain stable (not crash)
    assert stats["total_requests"] > 0
    print("\n✅ Stress test PASSED (system stable)")
```

---

## 📊 PERFORMANCE TARGETS

### Response Time Targets

| Load Level | Concurrent Users | Avg Response Time | P95 Response Time |
|------------|-----------------|-------------------|-------------------|
| **Normal** | 50 | < 2s | < 3s |
| **Peak** | 200 | < 5s | < 8s |
| **Stress** | 500+ | System stable | Graceful degradation |

### Throughput Targets

| Operation | Target RPS | Notes |
|-----------|-----------|-------|
| **Cost Collection** | 100 RPS | Per provider |
| **Analysis** | 50 RPS | With caching |
| **Recommendations** | 30 RPS | LLM dependent |
| **Execution** | 10 RPS | Resource intensive |

---

## ✅ ACCEPTANCE CRITERIA

### Must Have
- ✅ 15+ performance tests
- ✅ Load tests (normal, peak, stress)
- ✅ Performance benchmarks
- ✅ All tests passing
- ✅ Response time targets met
- ✅ Resource usage monitored

### Should Have
- ✅ Scalability tests
- ✅ Resource usage tests
- ✅ Metrics collection
- ✅ Performance reports

### Nice to Have
- ✅ Visual performance dashboards
- ✅ Historical performance tracking
- ✅ Automated performance regression detection

---

## 🚀 NEXT STEPS

After completing PART1:
1. Execute PART2 (Execution and Validation)
2. Run all performance tests
3. Analyze performance metrics
4. Generate performance reports
5. Document results
6. Identify optimization opportunities

---

**END OF PART1 SPECIFICATION**
