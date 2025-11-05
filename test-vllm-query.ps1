# Test vLLM queries directly

Write-Host "Testing vLLM Queries..." -ForegroundColor Cyan
Write-Host ""

$queries = @{
    "Request Count" = "vllm:request_success_total"
    "Requests Running" = "vllm:num_requests_running"
    "Queue Size" = "vllm:num_requests_waiting"
    "KV Cache Usage" = "vllm:kv_cache_usage_perc"
    "Latency Count" = "vllm:e2e_request_latency_seconds_count"
    "Tokens Generated" = "vllm:generation_tokens_total"
}

foreach ($name in $queries.Keys) {
    $query = $queries[$name]
    $url = "http://localhost:19092/api/v1/query?query=$query"
    
    try {
        $response = Invoke-WebRequest -Uri $url -UseBasicParsing
        $data = $response.Content | ConvertFrom-Json
        
        if ($data.data.result.Count -gt 0) {
            $value = $data.data.result[0].value[1]
            Write-Host "  [OK] $name : $value" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] $name : No data" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [ERROR] $name : Failed" -ForegroundColor Red
    }
}
