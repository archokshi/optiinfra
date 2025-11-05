"""
Simple E2E Test Runner - Uses Existing Services

Run this after starting docker-compose services.
"""
import subprocess
import sys

def main():
    print("\n" + "="*70)
    print("🧪 OptiInfra E2E Test Suite - Simple Runner")
    print("="*70 + "\n")
    
    print("Prerequisites:")
    print("  ✅ Docker services running (postgres, redis, clickhouse, qdrant)")
    print("  ✅ Python dependencies installed")
    print("\n")
    
    # Run tests without Docker Compose fixture
    test_commands = [
        {
            "name": "Quality Degradation Detection",
            "cmd": ["python", "-m", "pytest", 
                   "tests/e2e/test_additional_scenarios.py::test_quality_degradation_detection",
                   "-v", "-s", "--no-cov"]
        },
        {
            "name": "Instance Rightsizing",
            "cmd": ["python", "-m", "pytest",
                   "tests/e2e/test_additional_scenarios.py::test_instance_rightsizing",
                   "-v", "-s", "--no-cov"]
        },
        {
            "name": "Three-Way Conflict Resolution",
            "cmd": ["python", "-m", "pytest",
                   "tests/e2e/test_additional_scenarios.py::test_three_way_conflict_resolution",
                   "-v", "-s", "--no-cov"]
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_commands:
        print(f"\n{'='*70}")
        print(f"Running: {test['name']}")
        print(f"{'='*70}\n")
        
        try:
            result = subprocess.run(
                test['cmd'],
                capture_output=False,
                text=True
            )
            
            if result.returncode == 0:
                passed += 1
                print(f"\n✅ {test['name']} PASSED")
            else:
                failed += 1
                print(f"\n❌ {test['name']} FAILED")
                
        except Exception as e:
            failed += 1
            print(f"\n❌ {test['name']} ERROR: {e}")
    
    print(f"\n{'='*70}")
    print(f"Test Summary")
    print(f"{'='*70}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Total: {passed + failed}")
    print(f"{'='*70}\n")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
