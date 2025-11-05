"""
Performance Test Configuration and Fixtures.

Provides fixtures and utilities for performance testing.
"""

import pytest
import asyncio
import time
from typing import Dict, List
from datetime import datetime
import sys
import os

# Try to import psutil, but make it optional
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Resource monitoring will be limited.")


@pytest.fixture(scope="session")
def performance_config():
    """Performance test configuration."""
    return {
        "normal_load": {
            "concurrent_users": 50,
            "duration_seconds": 10,  # Reduced for faster tests
            "ramp_up_seconds": 2
        },
        "peak_load": {
            "concurrent_users": 200,
            "duration_seconds": 15,
            "ramp_up_seconds": 3
        },
        "stress_load": {
            "concurrent_users": 500,
            "duration_seconds": 20,
            "ramp_up_seconds": 5
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
            """Record response time in milliseconds."""
            self.metrics["response_times"].append(duration_ms)
        
        def record_error(self, error: str):
            """Record an error."""
            self.metrics["errors"].append(error)
        
        def record_cpu_usage(self):
            """Record current CPU usage."""
            if PSUTIL_AVAILABLE:
                self.metrics["cpu_usage"].append(psutil.cpu_percent(interval=0.1))
        
        def record_memory_usage(self):
            """Record current memory usage."""
            if PSUTIL_AVAILABLE:
                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                self.metrics["memory_usage"].append(memory_mb)
        
        def get_stats(self) -> Dict:
            """Calculate and return statistics."""
            response_times = self.metrics["response_times"]
            
            if not response_times:
                return {
                    "total_requests": 0,
                    "total_errors": 0,
                    "avg_response_time_ms": 0,
                    "min_response_time_ms": 0,
                    "max_response_time_ms": 0,
                    "p95_response_time_ms": 0,
                    "p99_response_time_ms": 0,
                    "error_rate_percent": 0,
                    "avg_cpu_percent": 0,
                    "avg_memory_mb": 0
                }
            
            sorted_times = sorted(response_times)
            
            return {
                "total_requests": len(response_times),
                "total_errors": len(self.metrics["errors"]),
                "avg_response_time_ms": sum(response_times) / len(response_times),
                "min_response_time_ms": min(response_times),
                "max_response_time_ms": max(response_times),
                "p95_response_time_ms": sorted_times[int(len(sorted_times) * 0.95)] if len(sorted_times) > 0 else 0,
                "p99_response_time_ms": sorted_times[int(len(sorted_times) * 0.99)] if len(sorted_times) > 0 else 0,
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
            """
            Generate load by running target function concurrently.
            
            Args:
                target_function: Async function to call
                concurrent_users: Number of concurrent users
                duration_seconds: Test duration
                ramp_up_seconds: Ramp-up time
                
            Returns:
                Test results
            """
            start_time = time.time()
            tasks = []
            
            # Create tasks
            for i in range(concurrent_users):
                # Ramp up gradually
                if ramp_up_seconds > 0 and i > 0:
                    delay = (ramp_up_seconds / concurrent_users) * i
                    await asyncio.sleep(delay / concurrent_users)
                
                task = asyncio.create_task(target_function())
                tasks.append(task)
            
            # Wait for duration
            await asyncio.sleep(duration_seconds)
            
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            completed = sum(1 for r in results if not isinstance(r, Exception))
            
            return {
                "duration": time.time() - start_time,
                "tasks_created": len(tasks),
                "tasks_completed": completed,
                "tasks_failed": len(tasks) - completed
            }
    
    return LoadGenerator()


@pytest.fixture
def benchmark_timer():
    """Simple benchmark timer fixture."""
    class BenchmarkTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            """Start the timer."""
            self.start_time = time.time()
        
        def stop(self):
            """Stop the timer."""
            self.end_time = time.time()
        
        def elapsed_ms(self) -> float:
            """Get elapsed time in milliseconds."""
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return 0
        
        def elapsed_seconds(self) -> float:
            """Get elapsed time in seconds."""
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
    
    return BenchmarkTimer()
