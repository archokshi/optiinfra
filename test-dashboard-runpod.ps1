Write-Host "Testing Dashboard API with RunPod provider..." -ForegroundColor Cyan
Write-Host ""

$url = "http://localhost:8001/api/v1/dashboard?provider=runpod"
Write-Host "URL: $url" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "Success!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Cost Agent:" -ForegroundColor Cyan
    Write-Host "  Status: $($data.agents.cost_agent.status)" -ForegroundColor Yellow
    Write-Host "  Monthly Cost: $($data.agents.cost_agent.monthly_cost)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Full Response:" -ForegroundColor Cyan
    Write-Host ($data | ConvertTo-Json -Depth 5)
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host "Response: $responseBody" -ForegroundColor Red
    }
}
