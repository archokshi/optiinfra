Write-Host "Testing dashboard method call directly..." -ForegroundColor Cyan

# Test the exact same call the dashboard makes
$url = "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/runpod/total?days=30"
Write-Host "URL: $url" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Total Cost: $($data.total_cost) $($data.currency)" -ForegroundColor Green
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
