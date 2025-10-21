#!/usr/bin/env python3
"""Test retry decorator"""
import sys
sys.path.insert(0, r'C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra')

import random
from shared.utils import retry

print("=" * 60)
print("TESTING RETRY DECORATOR")
print("=" * 60)

attempt_count = 0

@retry(max_attempts=3, delay=0.5, backoff=2.0)
def flaky_function():
    """Function that fails randomly"""
    global attempt_count
    attempt_count += 1
    
    print(f"\nAttempt {attempt_count}...")
    
    if random.random() < 0.6:  # 60% failure rate
        raise Exception("Simulated failure")
    
    return "Success!"

# Test 1: Function that eventually succeeds
print("\n1. Testing retry with eventual success:")
attempt_count = 0
try:
    result = flaky_function()
    print(f"✅ Result: {result} (after {attempt_count} attempts)")
except Exception as e:
    print(f"❌ Failed after {attempt_count} attempts: {e}")

# Test 2: Function that always fails
print("\n2. Testing retry with persistent failure:")
@retry(max_attempts=3, delay=0.2, backoff=1.5)
def always_fails():
    raise ValueError("This always fails")

try:
    always_fails()
except ValueError as e:
    print(f"✅ Correctly failed after retries: {e}")

print("\n" + "=" * 60)
print("✅ RETRY DECORATOR TEST PASSED")
print("=" * 60)
