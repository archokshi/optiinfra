import requests
import time

def test_port(port, description):
    print(f"\nTesting {description} (port {port})...")
    try:
        response = requests.get(f'http://host.docker.internal:{port}/api/v1/query?query=up', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ {description} is working!")
            data = response.json()
            results = data.get('data', {}).get('result', [])
            print(f"Active targets: {len(results)}")
            return True
        else:
            print(f"❌ Response: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Test different ports
ports_to_test = [
    (19092, "Port 9090 (original Prometheus)"),
    (19091, "Port 9091 (nginx - possible Prometheus proxy)"),
    (19400, "Port 9400 (GPU exporter)")
]

for port, desc in ports_to_test:
    test_port(port, desc)
    time.sleep(1)
