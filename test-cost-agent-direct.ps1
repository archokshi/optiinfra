# Test Cost Agent directly with ClickHouse query

Write-Host "=== Testing Cost Agent Data Access ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Data in ClickHouse:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT customer_id, provider, COUNT(*) as records, SUM(amount) as total FROM optiinfra_metrics.cost_metrics GROUP BY customer_id, provider FORMAT Pretty"

Write-Host ""
Write-Host "2. Testing Cost Agent API endpoints:" -ForegroundColor Yellow

$customerId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
$provider = "runpod"

Write-Host "   Testing: /api/v1/cost/$customerId/$provider/metrics" -ForegroundColor Cyan
try {
    $url = "http://localhost:8001/api/v1/cost/$customerId/$provider/metrics"
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "   [OK] Got $($data.metric_count) metrics" -ForegroundColor Green
    Write-Host "   Total Cost: $($data.metrics | Measure-Object -Property amount -Sum | Select-Object -ExpandProperty Sum)" -ForegroundColor Yellow
} catch {
    Write-Host "   [ERROR] $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "   Testing: /api/v1/cost/$customerId/$provider/total" -ForegroundColor Cyan
try {
    $url = "http://localhost:8001/api/v1/cost/$customerId/$provider/total"
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "   [OK] Total Cost: `$$($data.total_cost)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] $_" -ForegroundColor Red
}
