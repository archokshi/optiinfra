# Set Vultr API Key
$env:VULTR_API_KEY = "KO2ACJGYQUOAUU4WCOQKO7FJMHJAJK2H44HA"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Vultr API Key Set" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Connection Test
Write-Host "Running Connection Test..." -ForegroundColor Yellow
python test_vultr_connection.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Test 2: Full Collection Test
Write-Host "Running Full Collection Test..." -ForegroundColor Yellow
python test_vultr_full_collection.py
