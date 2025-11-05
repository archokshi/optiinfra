Write-Host "Checking cost_metrics_ts table in optiinfra database..." -ForegroundColor Cyan

$query = @"
SELECT 
    timestamp,
    customer_id,
    provider,
    instance_id,
    cost_type,
    amount,
    currency
FROM optiinfra.cost_metrics_ts 
WHERE customer_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' 
  AND provider = 'runpod'
ORDER BY timestamp DESC
LIMIT 5
"@

docker exec optiinfra-clickhouse clickhouse-client --query="$query"
