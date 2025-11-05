# Check when next collection will run

Write-Host "=== Next Scheduled Collection ===" -ForegroundColor Cyan
Write-Host ""

$currentTime = Get-Date
Write-Host "Current Time (PST): $($currentTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
Write-Host "Current Time (UTC): $($currentTime.ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Yellow
Write-Host ""

# Collections run every 15 minutes (at :00, :15, :30, :45)
$currentMinute = $currentTime.Minute
$nextMinutes = @(0, 15, 30, 45)
$nextCollectionMinute = $nextMinutes | Where-Object { $_ -gt $currentMinute } | Select-Object -First 1

if ($null -eq $nextCollectionMinute) {
    $nextCollectionMinute = 0
    $nextCollectionTime = $currentTime.AddHours(1)
} else {
    $nextCollectionTime = $currentTime
}

$nextCollectionTime = Get-Date -Year $nextCollectionTime.Year -Month $nextCollectionTime.Month -Day $nextCollectionTime.Day -Hour $nextCollectionTime.Hour -Minute $nextCollectionMinute -Second 0

Write-Host "Next Collection Time (PST): $($nextCollectionTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Green
Write-Host "Time Until Next Collection: $([math]::Round(($nextCollectionTime - $currentTime).TotalMinutes, 1)) minutes" -ForegroundColor Green
Write-Host ""

Write-Host "Checking Celery Beat logs for schedule..." -ForegroundColor Yellow
docker logs optiinfra-data-collector-beat --tail 50
