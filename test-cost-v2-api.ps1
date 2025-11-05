Write-Host "Testing Cost Agent V2 API..." -ForegroundColor Cyan

$customerId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
$provider = "runpod"

$url = "http://localhost:8001/api/v2/costs/$customerId/$provider/metrics"
Write-Host "URL: $url" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Success!" -ForegroundColor Green
    Write-Host "Metric Count: $($data.metric_count)" -ForegroundColor Cyan
    Write-Host "Total Cost: $($data.metrics | Measure-Object -Property amount -Sum | Select-Object -ExpandProperty Sum)" -ForegroundColor Yellow
    Write-Host ($data | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
