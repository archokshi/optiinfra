# Update RunPod credentials to use SSH tunnel ports
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod Live Demo"
    credentials = @{
        api_key = "demo-api-key"
        prometheus_url = "http://localhost:19092"
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

Write-Host "Updating RunPod credentials with SSH tunnel URL..."
Write-Host "Prometheus URL: http://localhost:19092"

$response = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

Write-Host "Response: $($response.StatusCode)"
Write-Host $response.Content
