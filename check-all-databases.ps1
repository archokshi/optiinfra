Write-Host "Checking all ClickHouse databases..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query="SHOW DATABASES"
