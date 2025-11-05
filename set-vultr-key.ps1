# Script to add VULTR_API_KEY to .env file
# Usage: .\set-vultr-key.ps1

Write-Host "=== OptiInfra - Set Vultr API Key ===" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path .env)) {
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
}

# Prompt for API key
Write-Host "Please enter your Vultr API Key:" -ForegroundColor Green
Write-Host "(You can find it at: https://my.vultr.com/settings/#settingsapi)" -ForegroundColor Gray
$apiKey = Read-Host "VULTR_API_KEY"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Host "Error: API key cannot be empty!" -ForegroundColor Red
    exit 1
}

# Read current .env content
$envContent = Get-Content .env -Raw

# Check if VULTR_API_KEY already exists
if ($envContent -match "VULTR_API_KEY=") {
    # Replace existing key
    $envContent = $envContent -replace "VULTR_API_KEY=.*", "VULTR_API_KEY=$apiKey"
    Write-Host "Updated existing VULTR_API_KEY" -ForegroundColor Yellow
} else {
    # Add new key
    $envContent += "`nVULTR_API_KEY=$apiKey`n"
    Write-Host "Added new VULTR_API_KEY" -ForegroundColor Green
}

# Write back to .env
$envContent | Set-Content .env -NoNewline

Write-Host ""
Write-Host "✓ VULTR_API_KEY has been set in .env file" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Restart the services:" -ForegroundColor White
Write-Host "   docker-compose restart data-collector data-collector-worker data-collector-beat" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Verify the key is set:" -ForegroundColor White
Write-Host "   docker exec optiinfra-data-collector-worker printenv | Select-String VULTR" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test collection:" -ForegroundColor White
Write-Host "   curl -Method POST -Uri http://localhost:8005/api/v1/collect/trigger -ContentType application/json -Body '{\"customer_id\":\"test\",\"provider\":\"vultr\",\"data_types\":[\"cost\"]}'" -ForegroundColor Gray
Write-Host ""
