# Restart Cost Agent to refresh data

Write-Host "=== Refreshing Cost Agent ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Restarting Cost Agent..." -ForegroundColor Yellow
docker restart optiinfra-cost-agent

Write-Host ""
Write-Host "2. Waiting for Cost Agent to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "3. Testing Cost Agent health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/live" -UseBasicParsing | ConvertFrom-Json
    Write-Host "   Status: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "   [ERROR] Cost Agent not responding yet" -ForegroundColor Red
}

Write-Host ""
Write-Host "4. Current cost data in ClickHouse:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT timestamp, instance_id, amount FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' ORDER BY timestamp DESC FORMAT Pretty"

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Hard refresh dashboard: Ctrl+Shift+R or Ctrl+F5" -ForegroundColor Yellow
Write-Host "2. Wait 1-2 minutes for agents to process new data" -ForegroundColor Yellow
Write-Host "3. If still showing old data, the portal UI may need restart" -ForegroundColor Yellow
