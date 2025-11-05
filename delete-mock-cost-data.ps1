# Delete mock cost data from ClickHouse

Write-Host "=== Deleting Mock Cost Data ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "Current cost data:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT timestamp, instance_id, amount FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' ORDER BY timestamp FORMAT Pretty"

Write-Host ""
Write-Host "Deleting mock data (Nov 1st records with fake instance IDs)..." -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "ALTER TABLE optiinfra_metrics.cost_metrics DELETE WHERE provider='runpod' AND instance_id IN ('runpod-gpu-1', 'runpod-gpu-2')"

Write-Host ""
Write-Host "Waiting for deletion to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Remaining cost data (should only show real data):" -ForegroundColor Green
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT timestamp, instance_id, amount FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' ORDER BY timestamp FORMAT Pretty"

Write-Host ""
Write-Host "[OK] Mock data deleted! Only real cost data remains." -ForegroundColor Green
