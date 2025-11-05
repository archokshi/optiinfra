-- Check all cost metrics
SELECT provider, COUNT(*) as count, MIN(collected_at) as first, MAX(collected_at) as last
FROM optiinfra_metrics.cost_metrics
GROUP BY provider
ORDER BY last DESC;

-- Check collection history
SELECT provider, status, started_at, completed_at, metrics_collected
FROM collection_history
ORDER BY started_at DESC
LIMIT 10;
