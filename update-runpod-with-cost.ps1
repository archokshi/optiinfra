# Update RunPod credentials with cost calculation parameters

Write-Host "=== Updating RunPod Credentials with Cost Parameters ===" -ForegroundColor Cyan
Write-Host ""

# Delete old credential
Write-Host "1. Deleting old RunPod credential..." -ForegroundColor Yellow
try {
    Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials/runpod?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" -Method DELETE -UseBasicParsing | Out-Null
    Write-Host "   [OK] Deleted old credential" -ForegroundColor Green
} catch {
    Write-Host "   [INFO] No existing credential to delete" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "2. Creating new RunPod credential with cost parameters..." -ForegroundColor Yellow

# Calculate pod start time (assuming it started 3 days ago based on your deployment)
# Adjust this to match when you actually started your RunPod pod
$podStartTime = (Get-Date).AddDays(-3).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss")

Write-Host "   Pod Start Time: $podStartTime UTC" -ForegroundColor Cyan
Write-Host "   Hourly Rate: `$0.50 (RunPod L4 GPU)" -ForegroundColor Cyan
Write-Host "   Instance ID: 6937f29fcae2 (your actual pod ID)" -ForegroundColor Cyan

$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod L4 with Cost Tracking"
    credentials = @{
        api_key = "demo-api-key"
        prometheus_url = "http://host.docker.internal:19092"
        hourly_rate = 0.50
        instance_id = "6937f29fcae2"
        pod_start_time = $podStartTime
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    Write-Host "   [OK] Credential created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "3. Cost Calculation:" -ForegroundColor Yellow
    $hoursRunning = ((Get-Date) - (Get-Date $podStartTime)).TotalHours
    $estimatedCost = $hoursRunning * 0.50
    Write-Host "   Hours Running: $([math]::Round($hoursRunning, 2)) hours" -ForegroundColor Cyan
    Write-Host "   Estimated Cost: `$$([math]::Round($estimatedCost, 2))" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Failed to create credential: $_" -ForegroundColor Red
    Write-Host "   Response: $($_.Exception.Response)" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Restart data collector: docker-compose up -d data-collector" -ForegroundColor Yellow
Write-Host "2. Trigger collection: .\quick-test.ps1" -ForegroundColor Yellow
Write-Host "3. Check cost data: .\view-cost-data.ps1" -ForegroundColor Yellow
