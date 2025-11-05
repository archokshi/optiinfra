Write-Host "Testing Cost Agent API..." -ForegroundColor Cyan

$url = "http://localhost:8001/api/v1/cost/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/runpod/metrics"
Write-Host "URL: $url" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Success!" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 5)
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Status: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}
