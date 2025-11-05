# Check collection status and timing

Write-Host "=== Collection Status Check ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Checking Celery Beat (Scheduler) Status..." -ForegroundColor Yellow
docker logs optiinfra-data-collector-worker --tail 20

Write-Host ""
Write-Host "2. Checking Recent Collections in ClickHouse..." -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT provider, COUNT(*) as total_metrics, MIN(collected_at) as first_collection, MAX(collected_at) as last_collection FROM optiinfra_metrics.performance_metrics WHERE provider='runpod' GROUP BY provider"

Write-Host ""
Write-Host "3. Checking Collection History..." -ForegroundColor Yellow
docker exec optiinfra-postgres psql -U optiinfra -d optiinfra -c "SELECT provider, status, metrics_collected, created_at AT TIME ZONE 'America/Los_Angeles' as created_at_pst FROM collection_history WHERE provider='runpod' ORDER BY created_at DESC LIMIT 10;"

Write-Host ""
Write-Host "4. Current Time Comparison..." -ForegroundColor Yellow
Write-Host "  Your Local Time (PST): $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host "  UTC Time: $(Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
