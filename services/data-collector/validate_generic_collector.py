"""
Generic Collector Validation Script
Tests Generic Collector independently
"""

import sys
import traceback

print("=" * 60)
print("GENERIC COLLECTOR VALIDATION")
print("=" * 60)

# Test 1: Import models
print("\n[1/5] Testing models import...")
try:
    from src.models.metrics import (
        Provider, PerformanceMetric, ResourceMetric, 
        ApplicationMetric, CollectionResult
    )
    print("✓ Models imported successfully")
    print(f"  - Provider enum has {len(Provider)} values")
    test1 = True
except Exception as e:
    print(f"✗ Models import failed: {e}")
    traceback.print_exc()
    test1 = False

# Test 2: Import base collector
print("\n[2/5] Testing base collector import...")
try:
    from src.collectors.base import BaseCollector
    print("✓ Base collector imported successfully")
    test2 = True
except Exception as e:
    print(f"✗ Base collector import failed: {e}")
    traceback.print_exc()
    test2 = False

# Test 3: Import Generic Collector
print("\n[3/5] Testing Generic Collector import...")
try:
    from src.collectors.generic_collector import GenericCollector, GenericCollectorConfig
    print("✓ Generic Collector imported successfully")
    test3 = True
except Exception as e:
    print(f"✗ Generic Collector import failed: {e}")
    traceback.print_exc()
    test3 = False

# Test 4: Create GenericCollectorConfig
print("\n[4/5] Testing GenericCollectorConfig creation...")
try:
    config = GenericCollectorConfig(
        provider="vultr",
        customer_id="test_customer",
        prometheus_url="http://localhost:9090",
        dcgm_url="http://localhost:9400",
        api_key="test_key"
    )
    config.validate()
    print("✓ GenericCollectorConfig created and validated")
    print(f"  - Provider: {config.provider}")
    print(f"  - Prometheus URL: {config.prometheus_url}")
    print(f"  - DCGM URL: {config.dcgm_url}")
    test4 = True
except Exception as e:
    print(f"✗ GenericCollectorConfig creation failed: {e}")
    traceback.print_exc()
    test4 = False

# Test 5: Create GenericCollector instance
print("\n[5/5] Testing GenericCollector instantiation...")
try:
    if test4:
        collector = GenericCollector(config)
        print("✓ GenericCollector instantiated successfully")
        print(f"  - Provider name: {collector.get_provider_name()}")
        print(f"  - Data type: {collector.get_data_type()}")
        test5 = True
    else:
        print("⊘ Skipped (config creation failed)")
        test5 = False
except Exception as e:
    print(f"✗ GenericCollector instantiation failed: {e}")
    traceback.print_exc()
    test5 = False

# Test 6: Import provider adapters
print("\n[6/6] Testing provider adapters import...")
try:
    from src.collectors.providers.vultr_api import VultrAPIAdapter
    from src.collectors.providers.runpod_api import RunPodAPIAdapter
    from src.collectors.providers.digitalocean_api import DigitalOceanAPIAdapter
    print("✓ Provider adapters imported successfully")
    test6 = True
except Exception as e:
    print(f"✗ Provider adapters import failed: {e}")
    traceback.print_exc()
    test6 = False

# Summary
print("\n" + "=" * 60)
tests = [test1, test2, test3, test4, test5, test6]
passed = sum(tests)
total = len(tests)
print(f"RESULTS: {passed}/{total} tests passed")
print("=" * 60)

if all(tests):
    print("✓ ALL VALIDATION TESTS PASSED")
    print("\nGeneric Collector is ready for testing!")
    sys.exit(0)
else:
    print("✗ SOME VALIDATION TESTS FAILED")
    print("\nPlease fix the errors above before proceeding.")
    sys.exit(1)
