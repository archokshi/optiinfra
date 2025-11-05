# OptiInfra - Convert HTML to PDF using Chrome/Edge
# This script converts the generated HTML files to PDF format

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OptiInfra HTML to PDF Converter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find Chrome or Edge executable
$chromePath = $null
$possiblePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $chromePath = $path
        Write-Host "Found browser: $path" -ForegroundColor Green
        break
    }
}

if (-not $chromePath) {
    Write-Host "ERROR: Chrome or Edge not found!" -ForegroundColor Red
    Write-Host "Please install Google Chrome or Microsoft Edge" -ForegroundColor Yellow
    pause
    exit 1
}

# Define HTML files to convert
$baseDir = "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra"
$files = @(
    @{
        html = "$baseDir\services\application-agent\PHASE4_Application_Agent_Comprehensive_Document.html"
        pdf = "$baseDir\services\application-agent\PHASE4_Application_Agent_Comprehensive_Document.pdf"
        name = "PHASE4 - Application Agent"
    },
    @{
        html = "$baseDir\services\resource-agent\PHASE3_Resource_Agent_Comprehensive_Document.html"
        pdf = "$baseDir\services\resource-agent\PHASE3_Resource_Agent_Comprehensive_Document.pdf"
        name = "PHASE3 - Resource Agent"
    },
    @{
        html = "$baseDir\services\performance-agent\PHASE2_Performance_Agent_Comprehensive_Document.html"
        pdf = "$baseDir\services\performance-agent\PHASE2_Performance_Agent_Comprehensive_Document.pdf"
        name = "PHASE2 - Performance Agent"
    },
    @{
        html = "$baseDir\services\cost-agent\PHASE1_Cost_Agent_Comprehensive_Document.html"
        pdf = "$baseDir\services\cost-agent\PHASE1_Cost_Agent_Comprehensive_Document.pdf"
        name = "PHASE1 - Cost Agent"
    },
    @{
        html = "$baseDir\services\orchestrator\PHASE0_Orchestrator_Comprehensive_Document.html"
        pdf = "$baseDir\services\orchestrator\PHASE0_Orchestrator_Comprehensive_Document.pdf"
        name = "PHASE0 - Orchestrator"
    }
)

# Convert each HTML to PDF
$count = 1
foreach ($file in $files) {
    Write-Host "[$count/5] Converting $($file.name)..." -ForegroundColor Yellow
    
    if (-not (Test-Path $file.html)) {
        Write-Host "   ERROR: HTML file not found: $($file.html)" -ForegroundColor Red
        $count++
        continue
    }
    
    # Use Chrome/Edge headless mode to print to PDF
    $args = @(
        "--headless",
        "--disable-gpu",
        "--print-to-pdf=`"$($file.pdf)`"",
        "--no-margins",
        "`"$($file.html)`""
    )
    
    try {
        Start-Process -FilePath $chromePath -ArgumentList $args -Wait -NoNewWindow
        
        if (Test-Path $file.pdf) {
            $pdfSize = (Get-Item $file.pdf).Length / 1KB
            Write-Host "   SUCCESS: PDF created ($([math]::Round($pdfSize, 2)) KB)" -ForegroundColor Green
        } else {
            Write-Host "   ERROR: PDF not created" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    $count++
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "PDF Conversion Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Generated PDFs:" -ForegroundColor Green
foreach ($file in $files) {
    if (Test-Path $file.pdf) {
        Write-Host "  [OK] $($file.pdf)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $($file.pdf)" -ForegroundColor Red
    }
}
Write-Host ""
pause
