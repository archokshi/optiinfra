# Fix RunPod credentials to use host.docker.internal

Write-Host "Deleting old credential..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials/runpod?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" -Method DELETE -UseBasicParsing | Out-Null
    Write-Host "  [OK] Deleted" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] Could not delete (may not exist)" -ForegroundColor Yellow
}

Write-Host "Creating new credential with host.docker.internal..." -ForegroundColor Yellow

$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod SSH Tunnel Fixed"
    credentials = @{
        api_key = "demo-api-key"
        prometheus_url = "http://host.docker.internal:19092"
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    Write-Host "  [OK] Credential created!" -ForegroundColor Green
    Write-Host "  Prometheus URL: http://host.docker.internal:19092" -ForegroundColor Cyan
} catch {
    Write-Host "  [ERROR] Failed: $_" -ForegroundColor Red
}
