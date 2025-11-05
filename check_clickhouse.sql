SELECT * FROM optiinfra_metrics.cost_metrics 
WHERE provider='runpod' 
ORDER BY collected_at DESC 
LIMIT 5;
