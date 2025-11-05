Write-Host "Checking ClickHouse tables..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query="SHOW TABLES"
