$body = @{
    customer_id = "demo-001"
    auto_approve = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://localhost:8001/spot-migration" -Method Post -Body $body -ContentType "application/json"

Write-Host "=== SPOT MIGRATION API TEST ===" -ForegroundColor Green
Write-Host ""
Write-Host "Request ID: $($response.request_id)" -ForegroundColor Cyan
Write-Host "Customer ID: $($response.customer_id)" -ForegroundColor Cyan
Write-Host "Status: $($response.workflow_status)" -ForegroundColor Yellow
Write-Host ""
Write-Host "Instances Analyzed: $($response.instances_analyzed)" -ForegroundColor White
Write-Host "Opportunities Found: $($response.opportunities_found)" -ForegroundColor White
Write-Host "Total Savings: `$$($response.total_savings)/month" -ForegroundColor Green
Write-Host "Final Savings: `$$($response.final_savings)/month" -ForegroundColor Green
Write-Host "Success: $($response.success)" -ForegroundColor $(if($response.success){"Green"}else{"Red"})
Write-Host ""
Write-Host "=== FULL RESPONSE ===" -ForegroundColor Green
$response | ConvertTo-Json -Depth 10
