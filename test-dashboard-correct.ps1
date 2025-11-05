Write-Host "Testing Dashboard with correct customer_id..." -ForegroundColor Cyan

$url = "http://localhost:8001/api/v1/dashboard?provider=runpod&customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
Write-Host "URL: $url" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Total Cost: $($data.metrics.cost.total_cost) $($data.metrics.cost.currency)" -ForegroundColor Green
    Write-Host "Monthly Cost: $($data.metrics.cost.monthly_cost) $($data.metrics.cost.currency)" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
