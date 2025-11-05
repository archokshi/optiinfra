# Analyze Cost Agent Data in Detail

Write-Host "=== COST AGENT DATA ANALYSIS ===" -ForegroundColor Cyan
Write-Host ""

Write-Host "1. Raw Cost Data from ClickHouse:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT timestamp, provider, cost_type, amount, currency, resource_type, collected_at FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' ORDER BY timestamp DESC FORMAT Pretty"

Write-Host ""
Write-Host "2. Cost Summary:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT cost_type, COUNT(*) as count, SUM(amount) as total_cost, MIN(timestamp) as first_record, MAX(timestamp) as last_record FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' GROUP BY cost_type FORMAT Pretty"

Write-Host ""
Write-Host "3. Cost Agent Analysis Results:" -ForegroundColor Yellow
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT * FROM optiinfra_analytics.cost_analysis WHERE provider='runpod' ORDER BY analysis_timestamp DESC LIMIT 5 FORMAT Pretty"

Write-Host ""
Write-Host "4. Expected Cost Calculation:" -ForegroundColor Yellow
Write-Host "  RunPod L4 GPU: `$0.50/hour" -ForegroundColor Cyan
Write-Host "  Workload ran for ~30 minutes = 0.5 hours" -ForegroundColor Cyan
Write-Host "  Expected cost: `$0.50 × 0.5 = `$0.25" -ForegroundColor Green
Write-Host ""
Write-Host "  If running for 1 hour: `$0.50" -ForegroundColor Cyan
Write-Host "  If running for 24 hours: `$12.00" -ForegroundColor Cyan
Write-Host "  Monthly (730 hours): `$365.00" -ForegroundColor Cyan
