# Check metrics in ClickHouse

Write-Host "Checking ClickHouse for RunPod metrics..." -ForegroundColor Cyan
Write-Host ""

Write-Host "Performance Metrics:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT metric_name, metric_value, created_at FROM optiinfra_metrics.performance_metrics WHERE provider='runpod' ORDER BY created_at DESC LIMIT 10"

Write-Host ""
Write-Host "Resource Metrics:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT metric_name, COUNT(*) FROM optiinfra_metrics.resource_metrics WHERE provider='runpod' GROUP BY metric_name"

Write-Host ""
Write-Host "Collection History:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT provider, status, metrics_collected, created_at FROM optiinfra_transactional.collection_history WHERE provider='runpod' ORDER BY created_at DESC LIMIT 5"
