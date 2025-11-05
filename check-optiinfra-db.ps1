Write-Host "Checking optiinfra database..." -ForegroundColor Cyan

docker exec optiinfra-clickhouse clickhouse-client --query="SHOW TABLES FROM optiinfra"
