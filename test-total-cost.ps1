Write-Host "Testing Total Cost API..." -ForegroundColor Cyan

$url = "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/runpod/total"
Write-Host "URL: $url" -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri $url -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "Success!" -ForegroundColor Green
    Write-Host ($data | ConvertTo-Json -Depth 3)
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
