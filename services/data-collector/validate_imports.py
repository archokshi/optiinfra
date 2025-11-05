"""
Import Validation Script
Tests that all imports work correctly
"""

import sys
import traceback

def test_import(module_path, description):
    """Test importing a module"""
    try:
        exec(f"from {module_path} import *")
        print(f"✓ {description}")
        return True
    except Exception as e:
        print(f"✗ {description}")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False

print("=" * 60)
print("IMPORT VALIDATION TEST")
print("=" * 60)

results = []

# Test 1: Models
results.append(test_import(
    "src.models.metrics",
    "Models (Provider, PerformanceMetric, etc.)"
))

# Test 2: Base Collector
results.append(test_import(
    "src.collectors.base",
    "Base Collector"
))

# Test 3: Generic Collector
results.append(test_import(
    "src.collectors.generic_collector",
    "Generic Collector"
))

# Test 4: Provider Adapters
results.append(test_import(
    "src.collectors.providers",
    "Provider Adapters (__init__)"
))

# Test 5: Config
results.append(test_import(
    "src.config",
    "Configuration"
))

print("\n" + "=" * 60)
print(f"RESULTS: {sum(results)}/{len(results)} imports successful")
print("=" * 60)

if all(results):
    print("✓ ALL IMPORTS VALIDATED SUCCESSFULLY")
    sys.exit(0)
else:
    print("✗ SOME IMPORTS FAILED")
    sys.exit(1)
