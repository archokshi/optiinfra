Write-Host "=== Testing Individual Cost Agent Methods ===" -ForegroundColor Cyan

$base = "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/runpod"

# Test total cost
Write-Host "`n1. Testing Total Cost..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base/total" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✅ Total Cost: $($data.total_cost) $($data.currency)" -ForegroundColor Green
} catch {
    Write-Host "❌ Total Cost failed: $_" -ForegroundColor Red
}

# Test metrics
Write-Host "`n2. Testing Metrics..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base/metrics" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✅ Metrics: $($data.metric_count) records" -ForegroundColor Green
} catch {
    Write-Host "❌ Metrics failed: $_" -ForegroundColor Red
}

# Test latest costs
Write-Host "`n3. Testing Latest Costs..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base/latest" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✅ Latest: $($data.metric_count) records" -ForegroundColor Green
} catch {
    Write-Host "❌ Latest failed: $_" -ForegroundColor Red
}

# Test trends
Write-Host "`n4. Testing Trends..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$base/trends" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✅ Trends: $($data.metric_count) records" -ForegroundColor Green
} catch {
    Write-Host "❌ Trends failed: $_" -ForegroundColor Red
}

Write-Host "`n=== Testing Dashboard ===" -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/v1/dashboard?provider=runpod" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✅ Dashboard Total Cost: $($data.metrics.cost.total_cost) $($data.metrics.cost.currency)" -ForegroundColor Green
    Write-Host "✅ Dashboard Daily Cost: $($data.metrics.cost.daily_cost)" -ForegroundColor Green
} catch {
    Write-Host "❌ Dashboard failed: $_" -ForegroundColor Red
}
