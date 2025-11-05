# Quick test collection
Write-Host "Triggering collection..." -ForegroundColor Cyan

$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    data_types = @("performance")
    async_mode = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing | Out-Null

Write-Host "Waiting for collection..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host "Checking logs..." -ForegroundColor Cyan
docker logs optiinfra-data-collector --tail 40
