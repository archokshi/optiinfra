"""
Test Generic Collector Configuration Validation
"""

import requests
import json

BASE_URL = "http://localhost:8005"

print("=" * 60)
print("GENERIC COLLECTOR CONFIGURATION VALIDATION TEST")
print("=" * 60)

# Test: Trigger collection without Prometheus URL configured
print("\n[TEST] Triggering collection for Vultr (no Prometheus URL)...")
try:
    payload = {
        "customer_id": "test_customer",
        "provider": "vultr",
        "data_types": ["cost"],
        "async_mode": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/collect/trigger",
        json=payload,
        timeout=10
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 400:
        print("\n✓ Validation working correctly - Provider not configured")
    elif response.status_code == 200:
        print("\n✓ Collection succeeded (Prometheus URL is configured)")
    else:
        print(f"\n✗ Unexpected status code: {response.status_code}")
        
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("Expected: HTTP 400 with message about Prometheus URL")
print("=" * 60)
