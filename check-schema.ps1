Write-Host "Checking ClickHouse schema..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query "DESCRIBE TABLE optiinfra_metrics.performance_metrics"

Write-Host ""
Write-Host "Checking actual data..." -ForegroundColor Cyan
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT * FROM optiinfra_metrics.performance_metrics WHERE provider='runpod' LIMIT 5"
