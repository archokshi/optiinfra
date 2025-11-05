$response = Invoke-WebRequest -Uri 'http://localhost:8005/api/v1/collectors/status?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
$json = $response.Content | ConvertFrom-Json
$runpod = $json.providers | Where-Object { $_.provider -eq 'runpod' }
$runpod | ConvertTo-Json -Depth 10
