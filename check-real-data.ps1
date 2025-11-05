Write-Host "Checking actual data in cost_metrics_ts..." -ForegroundColor Cyan

$query = @"
SELECT 
    timestamp,
    customer_id,
    cloud_provider as provider,
    instance_id,
    service_name as cost_type,
    cost_per_hour as amount,
    'USD' as currency
FROM optiinfra.cost_metrics_ts 
WHERE customer_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11' 
  AND cloud_provider = 'runpod'
ORDER BY timestamp DESC
LIMIT 5
"@

docker exec optiinfra-clickhouse clickhouse-client --query="$query"
