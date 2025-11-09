import requests

def test_collection():
    print("Testing REAL RunPod data collection...")
    
    r = requests.post(
        'http://localhost:8005/api/v1/collect/trigger',
        json={
            'provider': 'runpod',
            'customer_id': 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
            'data_types': ['performance', 'resource', 'cost']
        }
    )
    
    print(f'Status: {r.status_code}')
    print(f'Response: {r.text}')
    
    if r.status_code == 200:
        print("✅ Collection task queued successfully!")
        print("Monitor worker logs: docker logs optiinfra-data-collector-worker --tail 20")
    else:
        print("❌ Collection failed")

if __name__ == "__main__":
    test_collection()
