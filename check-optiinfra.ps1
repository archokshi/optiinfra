# OptiInfra RunPod Demo - Quick Verification
Write-Host "================================================"
Write-Host "OptiInfra RunPod Demo Verification"
Write-Host "================================================"
Write-Host ""

$customerId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
$provider = "runpod"

# Step 1: Check Services
Write-Host "Step 1: Checking OptiInfra Services..."
$dcStatus = docker ps --filter "name=optiinfra-data-collector" --format "{{.Status}}"
if ($dcStatus -like "*Up*") {
    Write-Host "  [OK] Data Collector: Running"
} else {
    Write-Host "  [FAIL] Data Collector: Not Running"
}

$chStatus = docker ps --filter "name=optiinfra-clickhouse" --format "{{.Status}}"
if ($chStatus -like "*Up*") {
    Write-Host "  [OK] ClickHouse: Running"
} else {
    Write-Host "  [FAIL] ClickHouse: Not Running"
}
Write-Host ""

# Step 2: Check Data Collector Health
Write-Host "Step 2: Checking Data Collector Health..."
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8005/health" -UseBasicParsing
    Write-Host "  [OK] Data Collector is healthy"
} catch {
    Write-Host "  [FAIL] Data Collector health check failed"
}
Write-Host ""

# Step 3: Check RunPod Credentials
Write-Host "Step 3: Checking RunPod Credentials..."
try {
    $url = "http://localhost:8005/api/v1/credentials/$provider`?customer_id=$customerId"
    $creds = Invoke-WebRequest -Uri $url -UseBasicParsing
    $credData = $creds.Content | ConvertFrom-Json
    Write-Host "  [OK] RunPod Credentials Found"
    Write-Host "  Provider: $($credData.provider)"
    Write-Host "  Status: $($credData.status)"
    if ($credData.credentials.prometheus_url) {
        Write-Host "  Prometheus URL: $($credData.credentials.prometheus_url)"
    }
} catch {
    Write-Host "  [WARN] RunPod Credentials Not Found"
    Write-Host "  You need to configure credentials first!"
}
Write-Host ""

# Step 4: Check Metrics in ClickHouse
Write-Host "Step 4: Checking Metrics in ClickHouse..."
$perfQuery = "SELECT COUNT(*) FROM optiinfra_metrics.performance_metrics WHERE provider = '$provider'"
$perfCount = docker exec optiinfra-clickhouse clickhouse-client --query $perfQuery 2>$null
Write-Host "  Performance Metrics: $perfCount records"

$costQuery = "SELECT COUNT(*) FROM optiinfra_metrics.cost_metrics WHERE provider = '$provider'"
$costCount = docker exec optiinfra-clickhouse clickhouse-client --query $costQuery 2>$null
Write-Host "  Cost Metrics: $costCount records"

$resQuery = "SELECT COUNT(*) FROM optiinfra_metrics.resource_metrics WHERE provider = '$provider'"
$resCount = docker exec optiinfra-clickhouse clickhouse-client --query $resQuery 2>$null
Write-Host "  Resource Metrics: $resCount records"
Write-Host ""

# Step 5: Check Dashboard API
Write-Host "Step 5: Checking Dashboard API..."
try {
    $dashUrl = "http://localhost:8005/api/v1/dashboard`?customer_id=$customerId`&provider=$provider"
    $dashboard = Invoke-WebRequest -Uri $dashUrl -UseBasicParsing
    $dashData = $dashboard.Content | ConvertFrom-Json
    Write-Host "  [OK] Dashboard API is working"
    Write-Host "  Total Cost: `$$($dashData.summary.total_cost)"
    Write-Host "  Cost Trends: $($dashData.cost_trends.Count) data points"
} catch {
    Write-Host "  [FAIL] Dashboard API failed: $_"
}
Write-Host ""

# Step 6: Recent Logs
Write-Host "Step 6: Recent Data Collector Logs (last 5 lines)..."
docker logs optiinfra-data-collector --tail 5 2>$null
Write-Host ""

Write-Host "================================================"
Write-Host "Verification Complete!"
Write-Host "================================================"
Write-Host ""
Write-Host "Next Steps:"
Write-Host "1. If credentials not found, configure them"
Write-Host "2. If metrics are 0, trigger collection"
Write-Host "3. View dashboard at http://localhost:3001/dashboard"
