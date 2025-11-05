# PHASE4-4.9: Performance Tests - Code Implementation Plan

**Phase**: PHASE4-4.9  
**Agent**: Application Agent  
**Estimated Time**: 25+20m = 45 minutes  
**Dependencies**: PHASE4-4.8 (API & Tests)

---

## Objective

Implement comprehensive performance testing using Locust for load testing, stress testing, and benchmarking the Application Agent APIs.

---

## What This Phase Creates

1. **Locust Load Tests** - Load testing scenarios
2. **Performance Benchmarks** - Baseline performance metrics
3. **Stress Tests** - System limits and breaking points
4. **Performance Reports** - HTML and CSV reports
5. **Monitoring Scripts** - Resource monitoring during tests

---

## File Structure

```
services/application-agent/
├── tests/
│   └── performance/
│       ├── __init__.py
│       ├── locustfile.py              # Main Locust test file
│       ├── test_load.py               # Load testing scenarios
│       ├── test_stress.py             # Stress testing scenarios
│       ├── test_spike.py              # Spike testing scenarios
│       └── test_endurance.py          # Endurance/soak testing
├── scripts/
│   ├── run_performance_tests.py       # Test runner script
│   ├── monitor_resources.py           # Resource monitoring
│   └── generate_report.py             # Report generation
└── performance/
    ├── results/                       # Test results
    ├── reports/                       # Generated reports
    └── benchmarks/                    # Baseline benchmarks
```

---

## Implementation Steps

### Step 1: Create Locust Test File (15 min)

**File**: `tests/performance/locustfile.py`

```python
"""
Locust Performance Tests for Application Agent

Run with: locust -f tests/performance/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, events
import json
import random
from datetime import datetime


class ApplicationAgentUser(HttpUser):
    """Simulated user for Application Agent."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Setup before tasks."""
        self.model_names = ["model-v1", "model-v2", "model-v3"]
        self.prompts = [
            "What is AI?",
            "Explain machine learning",
            "What is deep learning?",
            "How does NLP work?",
            "What are transformers?"
        ]
        self.responses = [
            "AI is artificial intelligence...",
            "Machine learning is a subset of AI...",
            "Deep learning uses neural networks...",
            "NLP processes natural language...",
            "Transformers are attention-based models..."
        ]
    
    @task(10)
    def analyze_quality(self):
        """Test quality analysis endpoint (highest weight)."""
        payload = {
            "prompt": random.choice(self.prompts),
            "response": random.choice(self.responses),
            "model_id": random.choice(self.model_names)
        }
        
        with self.client.post(
            "/quality/analyze",
            json=payload,
            catch_response=True,
            name="/quality/analyze"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
    
    @task(5)
    def get_quality_insights(self):
        """Test quality insights endpoint."""
        self.client.get("/quality/insights", name="/quality/insights")
    
    @task(3)
    def establish_baseline(self):
        """Test baseline establishment."""
        payload = {
            "model_name": random.choice(self.model_names),
            "config_hash": f"v{random.randint(1, 5)}.0.0",
            "sample_size": 100
        }
        self.client.post("/regression/baseline", json=payload, name="/regression/baseline")
    
    @task(3)
    def detect_regression(self):
        """Test regression detection."""
        payload = {
            "model_name": random.choice(self.model_names),
            "config_hash": "v1.0.0",
            "current_quality": random.uniform(70, 95)
        }
        self.client.post("/regression/detect", json=payload, name="/regression/detect")
    
    @task(2)
    def create_validation(self):
        """Test validation creation."""
        payload = {
            "name": f"validation-{random.randint(1, 1000)}",
            "model_name": random.choice(self.model_names),
            "baseline_quality": random.uniform(80, 90),
            "new_quality": random.uniform(85, 95)
        }
        self.client.post("/validation/create", json=payload, name="/validation/create")
    
    @task(2)
    def run_workflow(self):
        """Test workflow execution."""
        payload = {
            "model_name": random.choice(self.model_names),
            "prompt": random.choice(self.prompts),
            "response": random.choice(self.responses)
        }
        self.client.post("/workflow/validate", json=payload, name="/workflow/validate")
    
    @task(3)
    def get_analytics(self):
        """Test analytics endpoints."""
        endpoints = [
            "/analytics/summary",
            "/analytics/trends",
            "/analytics/comparison?models=model-v1,model-v2"
        ]
        endpoint = random.choice(endpoints)
        self.client.get(endpoint, name="/analytics/*")
    
    @task(2)
    def get_configuration(self):
        """Test configuration endpoints."""
        self.client.get("/config/current", name="/config/current")
    
    @task(1)
    def health_check(self):
        """Test health check."""
        self.client.get("/health", name="/health")
    
    @task(1)
    def admin_stats(self):
        """Test admin stats."""
        self.client.get("/admin/stats", name="/admin/stats")


class HighLoadUser(ApplicationAgentUser):
    """High load user with shorter wait times."""
    wait_time = between(0.5, 1.5)


class BurstUser(ApplicationAgentUser):
    """Burst user with no wait time."""
    wait_time = between(0, 0.5)


# Event handlers for custom metrics
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print(f"Performance test started at {datetime.now()}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print(f"Performance test stopped at {datetime.now()}")
    
    # Print summary statistics
    stats = environment.stats
    print("\n=== Performance Test Summary ===")
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Min response time: {stats.total.min_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time:.2f}ms")
    print(f"Requests per second: {stats.total.total_rps:.2f}")
```

### Step 2: Create Test Runner Script (10 min)

**File**: `scripts/run_performance_tests.py`

```python
"""
Performance Test Runner

Runs different performance test scenarios.
"""

import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime


def run_load_test(users=10, spawn_rate=2, duration="5m"):
    """Run load test."""
    print(f"\n=== Running Load Test ===")
    print(f"Users: {users}, Spawn Rate: {spawn_rate}, Duration: {duration}")
    
    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--host=http://localhost:8000",
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--headless",
        "--html", f"performance/reports/load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    ]
    
    subprocess.run(cmd)


def run_stress_test(max_users=100, spawn_rate=10, duration="10m"):
    """Run stress test."""
    print(f"\n=== Running Stress Test ===")
    print(f"Max Users: {max_users}, Spawn Rate: {spawn_rate}, Duration: {duration}")
    
    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--host=http://localhost:8000",
        "--users", str(max_users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration,
        "--headless",
        "--html", f"performance/reports/stress_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    ]
    
    subprocess.run(cmd)


def run_spike_test():
    """Run spike test."""
    print(f"\n=== Running Spike Test ===")
    
    # Normal load
    print("Phase 1: Normal load (10 users)")
    run_load_test(users=10, spawn_rate=10, duration="2m")
    
    time.sleep(5)
    
    # Spike
    print("Phase 2: Spike (100 users)")
    run_load_test(users=100, spawn_rate=100, duration="1m")
    
    time.sleep(5)
    
    # Back to normal
    print("Phase 3: Back to normal (10 users)")
    run_load_test(users=10, spawn_rate=10, duration="2m")


def run_endurance_test(users=20, duration="30m"):
    """Run endurance/soak test."""
    print(f"\n=== Running Endurance Test ===")
    print(f"Users: {users}, Duration: {duration}")
    
    cmd = [
        "locust",
        "-f", "tests/performance/locustfile.py",
        "--host=http://localhost:8000",
        "--users", str(users),
        "--spawn-rate", "5",
        "--run-time", duration,
        "--headless",
        "--html", f"performance/reports/endurance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    ]
    
    subprocess.run(cmd)


def main():
    """Main test runner."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_performance_tests.py [load|stress|spike|endurance|all]")
        sys.exit(1)
    
    test_type = sys.argv[1].lower()
    
    # Create directories
    Path("performance/reports").mkdir(parents=True, exist_ok=True)
    Path("performance/results").mkdir(parents=True, exist_ok=True)
    
    if test_type == "load":
        run_load_test()
    elif test_type == "stress":
        run_stress_test()
    elif test_type == "spike":
        run_spike_test()
    elif test_type == "endurance":
        run_endurance_test()
    elif test_type == "all":
        run_load_test()
        time.sleep(10)
        run_stress_test()
    else:
        print(f"Unknown test type: {test_type}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Step 3: Create Resource Monitor (10 min)

**File**: `scripts/monitor_resources.py`

```python
"""
Resource Monitoring Script

Monitors CPU, memory, and network during performance tests.
"""

import psutil
import time
import csv
from datetime import datetime
from pathlib import Path


def monitor_resources(duration_seconds=300, interval=1):
    """
    Monitor system resources.
    
    Args:
        duration_seconds: How long to monitor
        interval: Sampling interval in seconds
    """
    print(f"Monitoring resources for {duration_seconds} seconds...")
    
    # Create results directory
    Path("performance/results").mkdir(parents=True, exist_ok=True)
    
    # Output file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"performance/results/resources_{timestamp}.csv"
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'timestamp',
            'cpu_percent',
            'memory_percent',
            'memory_mb',
            'disk_read_mb',
            'disk_write_mb',
            'network_sent_mb',
            'network_recv_mb'
        ])
        
        start_time = time.time()
        disk_io_start = psutil.disk_io_counters()
        net_io_start = psutil.net_io_counters()
        
        while time.time() - start_time < duration_seconds:
            # Get current stats
            cpu = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            
            # Calculate deltas
            disk_read_mb = (disk_io.read_bytes - disk_io_start.read_bytes) / 1024 / 1024
            disk_write_mb = (disk_io.write_bytes - disk_io_start.write_bytes) / 1024 / 1024
            net_sent_mb = (net_io.bytes_sent - net_io_start.bytes_sent) / 1024 / 1024
            net_recv_mb = (net_io.bytes_recv - net_io_start.bytes_recv) / 1024 / 1024
            
            # Write row
            writer.writerow([
                datetime.now().isoformat(),
                cpu,
                memory.percent,
                memory.used / 1024 / 1024,
                disk_read_mb,
                disk_write_mb,
                net_sent_mb,
                net_recv_mb
            ])
            
            # Print current stats
            print(f"CPU: {cpu:5.1f}% | Memory: {memory.percent:5.1f}% | "
                  f"Disk R/W: {disk_read_mb:6.1f}/{disk_write_mb:6.1f} MB | "
                  f"Net S/R: {net_sent_mb:6.1f}/{net_recv_mb:6.1f} MB", end='\r')
            
            time.sleep(interval)
    
    print(f"\nResource monitoring complete. Results saved to {output_file}")


if __name__ == "__main__":
    import sys
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    monitor_resources(duration)
```

### Step 4: Update Requirements (5 min)

**File**: `requirements.txt` (add)

```txt
# Performance Testing
locust>=2.15.0
psutil>=5.9.0
```

---

## Performance Test Scenarios

### 1. Load Test
- **Users**: 10-50
- **Duration**: 5-10 minutes
- **Goal**: Baseline performance under normal load

### 2. Stress Test
- **Users**: 50-100+
- **Duration**: 10-15 minutes
- **Goal**: Find breaking point

### 3. Spike Test
- **Pattern**: Normal → Spike → Normal
- **Duration**: 5 minutes
- **Goal**: Test recovery from sudden load

### 4. Endurance Test
- **Users**: 20-30
- **Duration**: 30-60 minutes
- **Goal**: Test for memory leaks and degradation

---

## Performance Targets

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| Response Time (p50) | < 100ms | < 200ms | > 500ms |
| Response Time (p95) | < 200ms | < 500ms | > 1000ms |
| Response Time (p99) | < 500ms | < 1000ms | > 2000ms |
| Throughput | > 100 req/s | > 50 req/s | < 20 req/s |
| Error Rate | < 0.1% | < 1% | > 5% |
| CPU Usage | < 70% | < 85% | > 95% |
| Memory Usage | < 512MB | < 1GB | > 2GB |

---

## Success Criteria

- [ ] Locust tests created and working
- [ ] All test scenarios implemented
- [ ] Performance targets met
- [ ] Resource monitoring working
- [ ] Reports generated successfully
- [ ] No memory leaks detected
- [ ] System recovers from stress

---

## Estimated Time Breakdown

- Locust test file: 15 minutes
- Test runner script: 10 minutes
- Resource monitor: 10 minutes
- Testing and validation: 10 minutes

**Total**: 45 minutes

---

## Next Phase

**PHASE4-4.10**: Documentation (20+15m)
