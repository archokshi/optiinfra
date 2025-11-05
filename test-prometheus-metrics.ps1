# Test what metrics are available in Prometheus

Write-Host "Testing Prometheus Metrics..." -ForegroundColor Cyan
Write-Host ""

# Get all metric names
Write-Host "Fetching available metrics..." -ForegroundColor Yellow
$metricsResponse = Invoke-WebRequest -Uri "http://localhost:19092/api/v1/label/__name__/values" -UseBasicParsing
$metricsData = $metricsResponse.Content | ConvertFrom-Json

Write-Host "Total metrics available: $($metricsData.data.Count)" -ForegroundColor Green
Write-Host ""

# Filter for vLLM metrics
Write-Host "vLLM Metrics:" -ForegroundColor Yellow
$vllmMetrics = $metricsData.data | Where-Object { $_ -like "*vllm*" }
$vllmMetrics | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }

Write-Host ""

# Filter for GPU metrics
Write-Host "GPU/DCGM Metrics:" -ForegroundColor Yellow
$gpuMetrics = $metricsData.data | Where-Object { $_ -like "*DCGM*" -or $_ -like "*gpu*" }
$gpuMetrics | ForEach-Object { Write-Host "  $_" -ForegroundColor Cyan }

Write-Host ""

# Test a specific vLLM query
Write-Host "Testing vLLM request count query..." -ForegroundColor Yellow
$queryUrl = "http://localhost:19092/api/v1/query?query=vllm_request_duration_seconds_count"
$queryResponse = Invoke-WebRequest -Uri $queryUrl -UseBasicParsing
$queryData = $queryResponse.Content | ConvertFrom-Json

if ($queryData.data.result.Count -gt 0) {
    Write-Host "  [OK] Found data!" -ForegroundColor Green
    $value = $queryData.data.result[0].value[1]
    Write-Host "  Current value: $value" -ForegroundColor Cyan
} else {
    Write-Host "  [WARN] No data returned" -ForegroundColor Yellow
}
