# OptiInfra RunPod Workload Monitor
# Shows real-time data from your L4 GPU workload

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "OptiInfra RunPod Workload Monitor" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$customerId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
$runpodIp = "213.173.105.12"

Write-Host "Workload Info:" -ForegroundColor Yellow
Write-Host "  Pattern: 5 min @ 2 RPS, 5 min rest, 10 min @ 2 RPS, 10 min rest" -ForegroundColor Cyan
Write-Host "  Total Duration: 30 minutes" -ForegroundColor Cyan
Write-Host "  GPU: L4" -ForegroundColor Cyan
Write-Host "  RunPod IP: $runpodIp" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test RunPod Prometheus Directly
Write-Host "Step 1: Testing RunPod Prometheus (Direct)..." -ForegroundColor Yellow
try {
    $promUrl = "http://${runpodIp}:9091/api/v1/query?query=up"
    $promResponse = Invoke-WebRequest -Uri $promUrl -UseBasicParsing -TimeoutSec 5
    Write-Host "  [OK] Prometheus is accessible!" -ForegroundColor Green
    
    # Get vLLM metrics
    $vllmUrl = "http://${runpodIp}:9091/api/v1/query?query=vllm_request_duration_seconds_count"
    $vllmResponse = Invoke-WebRequest -Uri $vllmUrl -UseBasicParsing -TimeoutSec 5
    $vllmData = $vllmResponse.Content | ConvertFrom-Json
    if ($vllmData.data.result.Count -gt 0) {
        $requestCount = $vllmData.data.result[0].value[1]
        Write-Host "  [OK] vLLM Request Count: $requestCount" -ForegroundColor Green
    }
    
    # Get GPU utilization
    $gpuUrl = "http://${runpodIp}:9091/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL"
    $gpuResponse = Invoke-WebRequest -Uri $gpuUrl -UseBasicParsing -TimeoutSec 5
    $gpuData = $gpuResponse.Content | ConvertFrom-Json
    if ($gpuData.data.result.Count -gt 0) {
        $gpuUtil = $gpuData.data.result[0].value[1]
        Write-Host "  [OK] GPU Utilization: $gpuUtil%" -ForegroundColor Green
    }
} catch {
    Write-Host "  [ERROR] Cannot reach RunPod Prometheus!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 2: Trigger Collection
Write-Host "Step 2: Triggering Data Collection..." -ForegroundColor Yellow
try {
    $collectBody = @{
        customer_id = $customerId
        provider = "runpod"
        data_types = @("cost", "performance", "resource")
        async_mode = $false
    } | ConvertTo-Json

    $collectResponse = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $collectBody -ContentType "application/json" -UseBasicParsing
    $collectData = $collectResponse.Content | ConvertFrom-Json
    Write-Host "  [OK] Collection triggered!" -ForegroundColor Green
    Write-Host "  Status: $($collectData.status)" -ForegroundColor Cyan
    Write-Host "  Metrics Collected: $($collectData.metrics_collected)" -ForegroundColor Cyan
} catch {
    Write-Host "  [ERROR] Collection failed!" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 3: Check ClickHouse Data
Write-Host "Step 3: Checking Stored Metrics..." -ForegroundColor Yellow

Write-Host "  Performance Metrics:" -ForegroundColor Cyan
$perfQuery = "SELECT metric_name, COUNT(*) as count, AVG(metric_value) as avg_value FROM optiinfra_metrics.performance_metrics WHERE provider='runpod' GROUP BY metric_name ORDER BY count DESC LIMIT 10"
$perfResult = docker exec optiinfra-clickhouse clickhouse-client --query $perfQuery 2>$null
if ($perfResult) {
    Write-Host $perfResult -ForegroundColor White
} else {
    Write-Host "    No data yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Resource Metrics:" -ForegroundColor Cyan
$resQuery = "SELECT metric_name, COUNT(*) as count, AVG(metric_value) as avg_value FROM optiinfra_metrics.resource_metrics WHERE provider='runpod' GROUP BY metric_name ORDER BY count DESC LIMIT 10"
$resResult = docker exec optiinfra-clickhouse clickhouse-client --query $resQuery 2>$null
if ($resResult) {
    Write-Host $resResult -ForegroundColor White
} else {
    Write-Host "    No data yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "  Cost Metrics:" -ForegroundColor Cyan
$costQuery = "SELECT instance_type, COUNT(*) as count, AVG(cost_per_hour) as avg_cost FROM optiinfra_metrics.cost_metrics WHERE provider='runpod' GROUP BY instance_type LIMIT 5"
$costResult = docker exec optiinfra-clickhouse clickhouse-client --query $costQuery 2>$null
if ($costResult) {
    Write-Host $costResult -ForegroundColor White
} else {
    Write-Host "    No data yet" -ForegroundColor Yellow
}

Write-Host ""

# Step 4: Show Recent Collection History
Write-Host "Step 4: Collection History..." -ForegroundColor Yellow
$histQuery = "SELECT provider, status, metrics_collected, created_at FROM optiinfra_transactional.collection_history WHERE provider='runpod' ORDER BY created_at DESC LIMIT 3"
$histResult = docker exec optiinfra-clickhouse clickhouse-client --query $histQuery 2>$null
if ($histResult) {
    Write-Host $histResult -ForegroundColor White
} else {
    Write-Host "  No history yet" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Dashboard Summary
Write-Host "Step 5: Dashboard Data..." -ForegroundColor Yellow
try {
    $dashUrl = "http://localhost:8005/api/v1/dashboard?customer_id=$customerId&provider=runpod"
    $dashResponse = Invoke-WebRequest -Uri $dashUrl -UseBasicParsing
    $dashData = $dashResponse.Content | ConvertFrom-Json
    
    Write-Host "  Total Cost: `$$($dashData.summary.total_cost)" -ForegroundColor Cyan
    Write-Host "  Cost Trends: $($dashData.cost_trends.Count) data points" -ForegroundColor Cyan
    Write-Host "  Performance Metrics Available: $($dashData.performance_metrics.PSObject.Properties.Count) types" -ForegroundColor Cyan
} catch {
    Write-Host "  [WARN] Dashboard data not available yet" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "What You Should See:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. GPU Utilization" -ForegroundColor White
Write-Host "   - Spikes during 5-min and 10-min workload phases" -ForegroundColor Gray
Write-Host "   - Drops to ~0% during rest periods" -ForegroundColor Gray
Write-Host ""
Write-Host "2. vLLM Request Metrics" -ForegroundColor White
Write-Host "   - Request count increasing at 2 RPS during active phases" -ForegroundColor Gray
Write-Host "   - Latency metrics (avg response time)" -ForegroundColor Gray
Write-Host "   - Throughput (tokens/second)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Cost Metrics" -ForegroundColor White
Write-Host "   - L4 GPU cost per hour" -ForegroundColor Gray
Write-Host "   - Total cost accumulating over 30 minutes" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Agent Recommendations" -ForegroundColor White
Write-Host "   - Cost Agent: Analyze if L4 is right-sized" -ForegroundColor Gray
Write-Host "   - Performance Agent: Optimize for 2 RPS workload" -ForegroundColor Gray
Write-Host "   - Resource Agent: GPU utilization patterns" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. View Dashboard:" -ForegroundColor White
Write-Host "   Start-Process 'http://localhost:3001/dashboard'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Monitor in Real-Time:" -ForegroundColor White
Write-Host "   Run this script every 2-3 minutes to see updates" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Wait for Automatic Collection:" -ForegroundColor White
Write-Host "   Celery Beat will collect every 15 minutes automatically" -ForegroundColor Gray
Write-Host ""
