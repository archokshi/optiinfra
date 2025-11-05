-- Check if cost_metrics table exists and has data
SELECT 
    provider,
    COUNT(*) as metric_count,
    MIN(collected_at) as first_collection,
    MAX(collected_at) as last_collection
FROM optiinfra_metrics.cost_metrics
GROUP BY provider
ORDER BY last_collection DESC;

-- Check recent cost metrics
SELECT 
    provider,
    resource_id,
    cost_value,
    collected_at
FROM optiinfra_metrics.cost_metrics
ORDER BY collected_at DESC
LIMIT 10;
