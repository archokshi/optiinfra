Write-Host "Checking cost_agent database..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query="SHOW TABLES FROM cost_agent"
