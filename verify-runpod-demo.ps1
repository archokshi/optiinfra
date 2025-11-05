# OptiInfra RunPod Demo - Complete Verification Script
# This script verifies the entire data flow from RunPod to OptiInfra

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "🔍 OptiInfra RunPod Demo Verification" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$customerId = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
$provider = "runpod"

# Step 1: Check OptiInfra Services
Write-Host "📊 Step 1: Checking OptiInfra Services..." -ForegroundColor Yellow
Write-Host ""

$services = @(
    "optiinfra-data-collector",
    "optiinfra-portal",
    "optiinfra-clickhouse",
    "optiinfra-postgres",
    "optiinfra-cost-agent",
    "optiinfra-performance-agent",
    "optiinfra-resource-agent",
    "optiinfra-application-agent"
)

foreach ($service in $services) {
    $status = docker ps --filter "name=$service" --format "{{.Status}}" 2>$null
    if ($status -like "*Up*") {
        Write-Host "  ✅ $service : Running" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $service : Not Running" -ForegroundColor Red
    }
}

Write-Host ""

# Step 2: Check Data Collector Health
Write-Host "📊 Step 2: Checking Data Collector Health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://localhost:8005/health" -UseBasicParsing
    Write-Host "  ✅ Data Collector Health: OK" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Data Collector Health: Failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 3: Check RunPod Credentials
Write-Host "📊 Step 3: Checking RunPod Credentials..." -ForegroundColor Yellow
try {
    $creds = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials/$provider?customer_id=$customerId" -UseBasicParsing
    $credData = $creds.Content | ConvertFrom-Json
    Write-Host "  ✅ RunPod Credentials Found" -ForegroundColor Green
    Write-Host "  Provider: $($credData.provider)" -ForegroundColor Cyan
    Write-Host "  Status: $($credData.status)" -ForegroundColor Cyan
    if ($credData.credentials.prometheus_url) {
        Write-Host "  Prometheus URL: $($credData.credentials.prometheus_url)" -ForegroundColor Cyan
    }
} catch {
    Write-Host "  ❌ RunPod Credentials Not Found" -ForegroundColor Red
    Write-Host "  You need to configure credentials first!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Run this to configure:" -ForegroundColor Yellow
    Write-Host '  $body = @{' -ForegroundColor Gray
    Write-Host '      customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"' -ForegroundColor Gray
    Write-Host '      provider = "runpod"' -ForegroundColor Gray
    Write-Host '      credential_name = "RunPod Demo"' -ForegroundColor Gray
    Write-Host '      credentials = @{' -ForegroundColor Gray
    Write-Host '          api_key = "your-runpod-api-key"' -ForegroundColor Gray
    Write-Host '          prometheus_url = "http://YOUR_RUNPOD_IP:9091"' -ForegroundColor Gray
    Write-Host '      }' -ForegroundColor Gray
    Write-Host '      credential_type = "api_key"' -ForegroundColor Gray
    Write-Host '      permissions = "read_only"' -ForegroundColor Gray
    Write-Host '  } | ConvertTo-Json' -ForegroundColor Gray
    Write-Host '  Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json"' -ForegroundColor Gray
}
Write-Host ""

# Step 4: Check Collection History
Write-Host "📊 Step 4: Checking Collection History..." -ForegroundColor Yellow
try {
    $query = "SELECT provider, data_type, status, metrics_collected, created_at FROM optiinfra_transactional.collection_history WHERE customer_id = '$customerId' AND provider = '$provider' ORDER BY created_at DESC LIMIT 5;"
    $result = docker exec optiinfra-clickhouse clickhouse-client --query "$query" 2>$null
    if ($result) {
        Write-Host "  ✅ Collection History Found:" -ForegroundColor Green
        Write-Host $result -ForegroundColor Cyan
    } else {
        Write-Host "  ⚠️  No collection history yet" -ForegroundColor Yellow
        Write-Host "  Trigger collection to start collecting data" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ❌ Failed to query collection history" -ForegroundColor Red
}
Write-Host ""

# Step 5: Check Metrics in ClickHouse
Write-Host "📊 Step 5: Checking Metrics in ClickHouse..." -ForegroundColor Yellow

Write-Host "  Checking Performance Metrics..." -ForegroundColor Cyan
try {
    $query = "SELECT COUNT(*) FROM optiinfra_metrics.performance_metrics WHERE provider = '$provider';"
    $count = docker exec optiinfra-clickhouse clickhouse-client --query "$query" 2>$null
    if ([int]$count -gt 0) {
        Write-Host "    ✅ Performance Metrics: $count records" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Performance Metrics: 0 records" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ❌ Failed to query performance metrics" -ForegroundColor Red
}

Write-Host "  Checking Cost Metrics..." -ForegroundColor Cyan
try {
    $query = "SELECT COUNT(*) FROM optiinfra_metrics.cost_metrics WHERE provider = '$provider';"
    $count = docker exec optiinfra-clickhouse clickhouse-client --query "$query" 2>$null
    if ([int]$count -gt 0) {
        Write-Host "    ✅ Cost Metrics: $count records" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Cost Metrics: 0 records" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ❌ Failed to query cost metrics" -ForegroundColor Red
}

Write-Host "  Checking Resource Metrics..." -ForegroundColor Cyan
try {
    $query = "SELECT COUNT(*) FROM optiinfra_metrics.resource_metrics WHERE provider = '$provider';"
    $count = docker exec optiinfra-clickhouse clickhouse-client --query "$query" 2>$null
    if ([int]$count -gt 0) {
        Write-Host "    ✅ Resource Metrics: $count records" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Resource Metrics: 0 records" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ❌ Failed to query resource metrics" -ForegroundColor Red
}

Write-Host ""

# Step 6: Check Dashboard API
Write-Host "📊 Step 6: Checking Dashboard API..." -ForegroundColor Yellow
try {
    $dashboard = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/dashboard?customer_id=$customerId&provider=$provider" -UseBasicParsing
    $dashData = $dashboard.Content | ConvertFrom-Json
    Write-Host "  ✅ Dashboard API: OK" -ForegroundColor Green
    Write-Host "  Total Cost: `$$($dashData.summary.total_cost)" -ForegroundColor Cyan
    Write-Host "  Providers: $($dashData.summary.providers.Count)" -ForegroundColor Cyan
    Write-Host "  Cost Trends: $($dashData.cost_trends.Count) data points" -ForegroundColor Cyan
} catch {
    Write-Host "  ❌ Dashboard API: Failed" -ForegroundColor Red
    Write-Host "  Error: $_" -ForegroundColor Red
}
Write-Host ""

# Step 7: Check Recent Data Collector Logs
Write-Host "📊 Step 7: Recent Data Collector Logs..." -ForegroundColor Yellow
Write-Host "  Last 10 log entries:" -ForegroundColor Cyan
docker logs optiinfra-data-collector --tail 10 2>$null
Write-Host ""

# Step 8: Summary and Next Steps
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "📋 Summary & Next Steps" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "If you see ⚠️ warnings above, here's what to do:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣ Configure RunPod Credentials (if not done):" -ForegroundColor White
Write-Host '   $runpodIp = "YOUR_RUNPOD_IP"' -ForegroundColor Gray
Write-Host '   $body = @{' -ForegroundColor Gray
Write-Host '       customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"' -ForegroundColor Gray
Write-Host '       provider = "runpod"' -ForegroundColor Gray
Write-Host '       credential_name = "RunPod Demo"' -ForegroundColor Gray
Write-Host '       credentials = @{' -ForegroundColor Gray
Write-Host '           api_key = "your-api-key"' -ForegroundColor Gray
Write-Host '           prometheus_url = "http://$runpodIp:9091"' -ForegroundColor Gray
Write-Host '       }' -ForegroundColor Gray
Write-Host '       credential_type = "api_key"' -ForegroundColor Gray
Write-Host '       permissions = "read_only"' -ForegroundColor Gray
Write-Host '   } | ConvertTo-Json' -ForegroundColor Gray
Write-Host '   Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json"' -ForegroundColor Gray
Write-Host ""

Write-Host "2️⃣ Trigger Collection:" -ForegroundColor White
Write-Host '   $body = @{' -ForegroundColor Gray
Write-Host '       customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"' -ForegroundColor Gray
Write-Host '       provider = "runpod"' -ForegroundColor Gray
Write-Host '       data_types = @("cost", "performance", "resource")' -ForegroundColor Gray
Write-Host '       async_mode = $false' -ForegroundColor Gray
Write-Host '   } | ConvertTo-Json' -ForegroundColor Gray
Write-Host '   Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json"' -ForegroundColor Gray
Write-Host ""

Write-Host "3️⃣ View Dashboard:" -ForegroundColor White
Write-Host '   Start-Process "http://localhost:3001/dashboard"' -ForegroundColor Gray
Write-Host ""

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "✅ Verification Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
