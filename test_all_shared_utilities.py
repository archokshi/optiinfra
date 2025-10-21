#!/usr/bin/env python3
"""
Comprehensive test suite for all shared utilities
"""
import sys
import subprocess

print("=" * 70)
print("FOUNDATION-0.10: SHARED UTILITIES - COMPREHENSIVE TEST SUITE")
print("=" * 70)

test_scripts = [
    ('Configuration Module', 'test_shared_config.py'),
    ('Logging Module', 'test_shared_logging.py'),
    ('Retry Decorator', 'test_shared_retry.py'),
    ('Time Series Helpers', 'test_shared_timeseries.py'),
    ('Validators', 'test_shared_validators.py'),
    ('Metrics Collector', 'test_shared_metrics.py'),
]

results = []

for name, script in test_scripts:
    print(f"\n{'=' * 70}")
    print(f"Running: {name}")
    print('=' * 70)
    
    try:
        result = subprocess.run(
            ['python', script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"✅ {name} - PASSED")
            results.append((name, True))
        else:
            print(f"❌ {name} - FAILED")
            print(f"Error: {result.stderr}")
            results.append((name, False))
    except Exception as e:
        print(f"❌ {name} - ERROR: {e}")
        results.append((name, False))

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

passed = sum(1 for _, success in results if success)
total = len(results)

for name, success in results:
    status = "✅ PASSED" if success else "❌ FAILED"
    print(f"{name:.<50} {status}")

print("\n" + "=" * 70)
print(f"TOTAL: {passed}/{total} tests passed")
if passed == total:
    print("🎉 ALL TESTS PASSED! 🎉")
else:
    print(f"⚠️  {total - passed} test(s) failed")
print("=" * 70)

sys.exit(0 if passed == total else 1)
