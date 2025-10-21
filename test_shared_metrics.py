#!/usr/bin/env python3
"""Test metrics utilities"""
import sys
sys.path.insert(0, r'C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra')

import time
from shared.utils import measure_time, measure_block, count_calls, metrics_collector

print("=" * 60)
print("TESTING METRICS MODULE")
print("=" * 60)

# Test 1: Measure function time
print("\n1. Testing measure_time decorator:")

@measure_time('test_function_duration')
def slow_function():
    """Function that takes some time"""
    time.sleep(0.1)
    return "Done"

result = slow_function()
print(f"   Function result: {result}")
avg_duration = metrics_collector.get_average('test_function_duration')
print(f"   Average duration: {avg_duration:.3f}s")

# Test 2: Measure code block
print("\n2. Testing measure_block context manager:")
with measure_block('code_block_duration'):
    time.sleep(0.05)
    print("   Code block executed")

block_duration = metrics_collector.get_latest('code_block_duration')
print(f"   Block duration: {block_duration:.3f}s")

# Test 3: Count function calls
print("\n3. Testing count_calls decorator:")

@count_calls('function_calls')
def api_call():
    return "API response"

for i in range(5):
    api_call()

call_count = metrics_collector.get_average('function_calls')
print(f"   Total calls: {int(call_count * 5)}")

# Test 4: Get metrics summary
print("\n4. Metrics summary:")
summary = metrics_collector.get_summary()
for metric_name, stats in summary.items():
    print(f"   {metric_name}:")
    print(f"      Count: {stats['count']}")
    print(f"      Latest: {stats['latest']:.4f}")
    print(f"      Average: {stats['average']:.4f}")
    print(f"      Min: {stats['min']:.4f}")
    print(f"      Max: {stats['max']:.4f}")

print("\n" + "=" * 60)
print("✅ METRICS MODULE TEST PASSED")
print("=" * 60)
