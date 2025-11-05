Write-Host "Checking all data in cost_metrics_ts..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query="SELECT COUNT(*) FROM optiinfra.cost_metrics_ts"
