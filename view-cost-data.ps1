Write-Host "=== COST DATA DETAILS ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "All Cost Records:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT * FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' ORDER BY timestamp DESC FORMAT Pretty"

Write-Host ""
Write-Host "Cost Summary by Hour:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT timestamp, amount, currency FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' ORDER BY timestamp FORMAT Pretty"
