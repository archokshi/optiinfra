# Test Prometheus query directly with the exact format the collector uses

$prometheusUrl = "http://localhost:19092"
$query = "vllm:request_success_total"

Write-Host "Testing query: $query" -ForegroundColor Cyan

$url = "$prometheusUrl/api/v1/query"
$response = Invoke-WebRequest -Uri $url -Method Get -Body @{query=$query} -UseBasicParsing
$data = $response.Content | ConvertFrom-Json

Write-Host "Status: $($data.status)" -ForegroundColor Yellow
Write-Host "Result count: $($data.data.result.Count)" -ForegroundColor Yellow

if ($data.data.result.Count -gt 0) {
    Write-Host "Value: $($data.data.result[0].value[1])" -ForegroundColor Green
} else {
    Write-Host "No results!" -ForegroundColor Red
}

# Now test with histogram quantile
Write-Host ""
Write-Host "Testing histogram quantile..." -ForegroundColor Cyan
$query2 = "histogram_quantile(0.50, rate(vllm:e2e_request_latency_seconds_bucket[5m]))"
$response2 = Invoke-WebRequest -Uri $url -Method Get -Body @{query=$query2} -UseBasicParsing
$data2 = $response2.Content | ConvertFrom-Json

Write-Host "Status: $($data2.status)" -ForegroundColor Yellow
Write-Host "Result count: $($data2.data.result.Count)" -ForegroundColor Yellow

if ($data2.data.result.Count -gt 0) {
    Write-Host "Value: $($data2.data.result[0].value[1])" -ForegroundColor Green
} else {
    Write-Host "No results (might need more data points)" -ForegroundColor Yellow
}
