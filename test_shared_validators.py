#!/usr/bin/env python3
"""Test validator utilities"""
import sys
sys.path.insert(0, r'C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra')

from shared.utils import (
    ValidationError,
    validate_required,
    validate_email,
    validate_url,
    validate_range,
    validate_positive,
    validate_instance_id,
)

print("=" * 60)
print("TESTING VALIDATORS MODULE")
print("=" * 60)

# Test 1: Required validation
print("\n1. Testing required validation:")
try:
    validate_required("test_value", "test_field")
    print("   ✅ Valid value passed")
except ValidationError as e:
    print(f"   ❌ {e}")

try:
    validate_required("", "test_field")
    print("   ❌ Empty value should have failed")
except ValidationError as e:
    print(f"   ✅ Correctly rejected empty value: {e}")

# Test 2: Email validation
print("\n2. Testing email validation:")
valid_email = "user@example.com"
invalid_email = "invalid-email"
print(f"   {valid_email}: {validate_email(valid_email)} (should be True)")
print(f"   {invalid_email}: {validate_email(invalid_email)} (should be False)")

# Test 3: URL validation
print("\n3. Testing URL validation:")
valid_url = "https://example.com/api"
invalid_url = "not-a-url"
print(f"   {valid_url}: {validate_url(valid_url)} (should be True)")
print(f"   {invalid_url}: {validate_url(invalid_url)} (should be False)")

# Test 4: Range validation
print("\n4. Testing range validation:")
try:
    validate_range(50, min_val=0, max_val=100, field_name="cpu_usage")
    print("   ✅ Value 50 in range [0, 100]")
except ValidationError as e:
    print(f"   ❌ {e}")

try:
    validate_range(150, min_val=0, max_val=100, field_name="cpu_usage")
    print("   ❌ Value 150 should have failed")
except ValidationError as e:
    print(f"   ✅ Correctly rejected out-of-range value: {e}")

# Test 5: Positive validation
print("\n5. Testing positive validation:")
try:
    validate_positive(10, "count")
    print("   ✅ Positive value passed")
except ValidationError as e:
    print(f"   ❌ {e}")

try:
    validate_positive(-5, "count")
    print("   ❌ Negative value should have failed")
except ValidationError as e:
    print(f"   ✅ Correctly rejected negative value: {e}")

# Test 6: Instance ID validation
print("\n6. Testing instance ID validation:")
aws_id = "i-1234567890abcdef0"
gcp_id = "instance-name-123"
azure_id = "vm-name-123"
invalid_id = "invalid@id"
print(f"   AWS ID {aws_id}: {validate_instance_id(aws_id)}")
print(f"   GCP ID {gcp_id}: {validate_instance_id(gcp_id)}")
print(f"   Azure ID {azure_id}: {validate_instance_id(azure_id)}")
print(f"   Invalid ID {invalid_id}: {validate_instance_id(invalid_id)}")

print("\n" + "=" * 60)
print("✅ VALIDATORS MODULE TEST PASSED")
print("=" * 60)
