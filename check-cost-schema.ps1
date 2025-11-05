Write-Host "Checking ClickHouse cost_metrics schema..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query "DESCRIBE optiinfra_metrics.cost_metrics"
