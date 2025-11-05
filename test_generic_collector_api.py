"""
End-to-End Test for Generic Collector API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8005"

print("=" * 60)
print("GENERIC COLLECTOR END-TO-END TEST")
print("=" * 60)

# Test 1: Health Check
print("\n[1/4] Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Health check passed")
        print(f"  - Service: {data['service']}")
        print(f"  - Status: {data['status']}")
        print(f"  - Dependencies: {data['dependencies']}")
    else:
        print(f"✗ Health check failed: {response.status_code}")
except Exception as e:
    print(f"✗ Health check error: {e}")

# Test 2: Root Endpoint
print("\n[2/4] Testing root endpoint...")
try:
    response = requests.get(f"{BASE_URL}/")
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Root endpoint passed")
        print(f"  - Service: {data['service']}")
        print(f"  - Endpoints: {list(data['endpoints'].keys())}")
    else:
        print(f"✗ Root endpoint failed: {response.status_code}")
except Exception as e:
    print(f"✗ Root endpoint error: {e}")

# Test 3: Trigger Collection (Synchronous Mode)
print("\n[3/4] Testing collection trigger (sync mode)...")
try:
    payload = {
        "customer_id": "test_customer_e2e",
        "provider": "vultr",  # Generic provider
        "data_types": ["cost"],
        "async_mode": False  # Synchronous for immediate response
    }
    
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/collect/trigger",
        json=payload,
        timeout=60
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Collection triggered successfully")
        print(f"  - Task ID: {data['task_id']}")
        print(f"  - Status: {data['status']}")
        print(f"  - Message: {data['message']}")
    else:
        print(f"✗ Collection failed: {response.status_code}")
        print(f"  Response: {response.text}")
except Exception as e:
    print(f"✗ Collection error: {e}")

# Test 4: Trigger Collection (Async Mode)
print("\n[4/4] Testing collection trigger (async mode)...")
try:
    payload = {
        "customer_id": "test_customer_async",
        "provider": "digitalocean",  # Another generic provider
        "data_types": ["cost"],
        "async_mode": True  # Async mode
    }
    
    print(f"  Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/v1/collect/trigger",
        json=payload,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Async collection queued successfully")
        print(f"  - Task ID: {data['task_id']}")
        print(f"  - Status: {data['status']}")
        print(f"  - Async Mode: {data.get('async_mode', False)}")
    else:
        print(f"✗ Async collection failed: {response.status_code}")
        print(f"  Response: {response.text}")
except Exception as e:
    print(f"✗ Async collection error: {e}")

print("\n" + "=" * 60)
print("END-TO-END TEST COMPLETE")
print("=" * 60)
