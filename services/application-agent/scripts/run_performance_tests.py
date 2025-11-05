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
