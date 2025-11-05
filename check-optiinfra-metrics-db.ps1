Write-Host "Checking optiinfra_metrics database..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query="SHOW TABLES FROM optiinfra_metrics"
