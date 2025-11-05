# Test SSH Tunnel and Trigger Collection

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "RunPod SSH Tunnel Test & Collection" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Test SSH Tunnel Connectivity
Write-Host "Step 1: Testing SSH Tunnel Connectivity..." -ForegroundColor Yellow

Write-Host "  Testing vLLM (port 18100)..." -ForegroundColor Cyan
try {
    $vllm = Invoke-WebRequest -Uri "http://localhost:18100/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  [OK] vLLM is accessible!" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] vLLM not accessible. Is SSH tunnel running?" -ForegroundColor Red
    Write-Host "  Run: ssh -L 18100:localhost:8100 -L 19092:localhost:9092 -L 19401:localhost:9401 root@213.173.105.12 -p 55114" -ForegroundColor Yellow
    exit 1
}

Write-Host "  Testing Prometheus (port 19092)..." -ForegroundColor Cyan
try {
    $prom = Invoke-WebRequest -Uri "http://localhost:19092/-/healthy" -UseBasicParsing -TimeoutSec 5
    Write-Host "  [OK] Prometheus is accessible!" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] Prometheus not accessible" -ForegroundColor Red
    exit 1
}

Write-Host "  Testing GPU Metrics (port 19401)..." -ForegroundColor Cyan
try {
    $gpu = Invoke-WebRequest -Uri "http://localhost:19401/metrics" -UseBasicParsing -TimeoutSec 5
    Write-Host "  [OK] GPU Metrics accessible!" -ForegroundColor Green
} catch {
    Write-Host "  [WARN] GPU Metrics not accessible (optional)" -ForegroundColor Yellow
}

Write-Host ""

# Step 2: Get some sample metrics
Write-Host "Step 2: Checking RunPod Metrics..." -ForegroundColor Yellow

Write-Host "  Querying vLLM request count..." -ForegroundColor Cyan
try {
    $vllmMetrics = Invoke-WebRequest -Uri "http://localhost:19092/api/v1/query?query=vllm_request_duration_seconds_count" -UseBasicParsing
    $vllmData = $vllmMetrics.Content | ConvertFrom-Json
    if ($vllmData.data.result.Count -gt 0) {
        $count = $vllmData.data.result[0].value[1]
        Write-Host "  vLLM Total Requests: $count" -ForegroundColor Green
    }
} catch {
    Write-Host "  [WARN] Could not get vLLM metrics" -ForegroundColor Yellow
}

Write-Host "  Querying GPU utilization..." -ForegroundColor Cyan
try {
    $gpuMetrics = Invoke-WebRequest -Uri "http://localhost:19092/api/v1/query?query=DCGM_FI_DEV_GPU_UTIL" -UseBasicParsing
    $gpuData = $gpuMetrics.Content | ConvertFrom-Json
    if ($gpuData.data.result.Count -gt 0) {
        $util = $gpuData.data.result[0].value[1]
        Write-Host "  GPU Utilization: $util%" -ForegroundColor Green
    }
} catch {
    Write-Host "  [WARN] Could not get GPU metrics" -ForegroundColor Yellow
}

Write-Host ""

# Step 3: Update OptiInfra Credentials
Write-Host "Step 3: Updating OptiInfra Credentials..." -ForegroundColor Yellow

# First, try to delete existing credential
try {
    Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials/runpod?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11" -Method DELETE -UseBasicParsing | Out-Null
    Write-Host "  Deleted old credential" -ForegroundColor Cyan
} catch {
    Write-Host "  No existing credential to delete" -ForegroundColor Gray
}

# Create new credential with tunnel URL
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod SSH Tunnel"
    credentials = @{
        api_key = "demo-api-key"
        prometheus_url = "http://localhost:19092"
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

try {
    $credResponse = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    Write-Host "  [OK] Credentials updated!" -ForegroundColor Green
    Write-Host "  Prometheus URL: http://localhost:19092" -ForegroundColor Cyan
} catch {
    Write-Host "  [ERROR] Failed to update credentials: $_" -ForegroundColor Red
}

Write-Host ""

# Step 4: Trigger Collection
Write-Host "Step 4: Triggering Data Collection..." -ForegroundColor Yellow
Write-Host "  This will take 30-60 seconds..." -ForegroundColor Cyan

$collectBody = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    data_types = @("cost", "performance", "resource")
    async_mode = $false
} | ConvertTo-Json

try {
    $collectResponse = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $collectBody -ContentType "application/json" -UseBasicParsing
    $collectData = $collectResponse.Content | ConvertFrom-Json
    
    Write-Host "  [OK] Collection completed!" -ForegroundColor Green
    Write-Host "  Status: $($collectData.status)" -ForegroundColor Cyan
    Write-Host "  Metrics Collected: $($collectData.metrics_collected)" -ForegroundColor Cyan
    Write-Host "  Message: $($collectData.message)" -ForegroundColor Cyan
} catch {
    Write-Host "  [ERROR] Collection failed: $_" -ForegroundColor Red
}

Write-Host ""

# Step 5: Verify Data in ClickHouse
Write-Host "Step 5: Verifying Collected Data..." -ForegroundColor Yellow

$perfCount = docker exec optiinfra-clickhouse clickhouse-client --query "SELECT COUNT(*) FROM optiinfra_metrics.performance_metrics WHERE provider='runpod'" 2>$null
Write-Host "  Performance Metrics: $perfCount records" -ForegroundColor Cyan

$resCount = docker exec optiinfra-clickhouse clickhouse-client --query "SELECT COUNT(*) FROM optiinfra_metrics.resource_metrics WHERE provider='runpod'" 2>$null
Write-Host "  Resource Metrics: $resCount records" -ForegroundColor Cyan

$costCount = docker exec optiinfra-clickhouse clickhouse-client --query "SELECT COUNT(*) FROM optiinfra_metrics.cost_metrics WHERE provider='runpod'" 2>$null
Write-Host "  Cost Metrics: $costCount records" -ForegroundColor Cyan

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. View Dashboard:" -ForegroundColor White
Write-Host "   Start-Process 'http://localhost:3001/dashboard'" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Run Workload Again:" -ForegroundColor White
Write-Host "   python3 /root/vllm_demo/workload_test.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Monitor Real-Time:" -ForegroundColor White
Write-Host "   Run this script again in 2-3 minutes" -ForegroundColor Gray
Write-Host ""
