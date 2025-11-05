# Check Cost Agent status and data

Write-Host "=== Cost Agent Status Check ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Cost Agent Health:" -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing | ConvertFrom-Json
    Write-Host "   Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Cost Agent not responding" -ForegroundColor Red
}

Write-Host ""
Write-Host "2. Cost Agent Metrics for RunPod:" -ForegroundColor Yellow
try {
    $metrics = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/cost/metrics?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11&provider=runpod" -UseBasicParsing | ConvertFrom-Json
    Write-Host "   Response: $($metrics | ConvertTo-Json -Depth 5)" -ForegroundColor Cyan
} catch {
    Write-Host "   [ERROR] Failed to get metrics: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "3. Raw ClickHouse Data (what Cost Agent should see):" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT COUNT(*) as total_records, SUM(amount) as total_cost, MAX(timestamp) as latest_timestamp FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' FORMAT Pretty"

Write-Host ""
Write-Host "4. Cost Agent Logs:" -ForegroundColor Yellow
docker logs optiinfra-cost-agent --tail 20
