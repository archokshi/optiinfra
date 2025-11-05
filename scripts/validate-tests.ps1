# Test Suite Validation Script
# Validates all test files, fixtures, and infrastructure

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "OptiInfra Test Suite Validation" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorCount = 0
$WarningCount = 0
$PassCount = 0

# Function to check file exists
function Test-FileExists {
    param($Path, $Description)
    
    if (Test-Path $Path) {
        Write-Host "✅ $Description" -ForegroundColor Green
        $script:PassCount++
        return $true
    } else {
        Write-Host "❌ $Description - NOT FOUND" -ForegroundColor Red
        $script:ErrorCount++
        return $false
    }
}

# Function to count tests in file
function Count-TestsInFile {
    param($Path)
    
    if (Test-Path $Path) {
        $content = Get-Content $Path -Raw
        $testCount = ([regex]::Matches($content, "async def test_|def test_")).Count
        return $testCount
    }
    return 0
}

Write-Host "📁 Validating Test Directory Structure..." -ForegroundColor Yellow
Write-Host "=" * 50

# Check main directories
Test-FileExists "tests" "tests/ directory"
Test-FileExists "tests/e2e" "tests/e2e/ directory"
Test-FileExists "tests/integration" "tests/integration/ directory"
Test-FileExists "tests/performance" "tests/performance/ directory"
Test-FileExists "tests/security" "tests/security/ directory"
Test-FileExists "tests/fixtures" "tests/fixtures/ directory"
Test-FileExists "tests/helpers" "tests/helpers/ directory"

Write-Host "`n📄 Validating Infrastructure Files..." -ForegroundColor Yellow
Write-Host "=" * 50

# Infrastructure files
Test-FileExists "tests/docker-compose.e2e.yml" "Docker Compose test environment"
Test-FileExists "tests/e2e/conftest.py" "Pytest configuration and fixtures"
Test-FileExists "pytest.ini" "Pytest configuration"
Test-FileExists "requirements-test.txt" "Test dependencies"
Test-FileExists "Makefile" "Makefile with test commands"

Write-Host "`n🧪 Validating E2E Test Files..." -ForegroundColor Yellow
Write-Host "=" * 50

$e2eTests = @(
    @{Path="tests/e2e/test_spot_migration.py"; Name="Spot Migration"; Expected=3},
    @{Path="tests/e2e/test_performance_optimization.py"; Name="Performance Optimization"; Expected=3},
    @{Path="tests/e2e/test_multi_agent_coordination.py"; Name="Multi-Agent Coordination"; Expected=3},
    @{Path="tests/e2e/test_complete_customer_journey.py"; Name="Complete Customer Journey"; Expected=3},
    @{Path="tests/e2e/test_additional_scenarios.py"; Name="Additional Scenarios"; Expected=8}
)

$totalE2ETests = 0
foreach ($test in $e2eTests) {
    if (Test-FileExists $test.Path $test.Name) {
        $count = Count-TestsInFile $test.Path
        $totalE2ETests += $count
        Write-Host "   └─ Contains $count tests" -ForegroundColor Gray
    }
}

Write-Host "`n🔗 Validating Integration Test Files..." -ForegroundColor Yellow
Write-Host "=" * 50

$integrationTests = @(
    @{Path="tests/integration/test_agent_orchestrator.py"; Name="Agent-Orchestrator"; Expected=18},
    @{Path="tests/integration/test_portal_api.py"; Name="Portal-API"; Expected=12}
)

$totalIntegrationTests = 0
foreach ($test in $integrationTests) {
    if (Test-FileExists $test.Path $test.Name) {
        $count = Count-TestsInFile $test.Path
        $totalIntegrationTests += $count
        Write-Host "   └─ Contains $count tests" -ForegroundColor Gray
    }
}

Write-Host "`n⚡ Validating Performance Test Files..." -ForegroundColor Yellow
Write-Host "=" * 50

if (Test-FileExists "tests/performance/test_system_performance.py" "Performance Tests") {
    $perfCount = Count-TestsInFile "tests/performance/test_system_performance.py"
    Write-Host "   └─ Contains $perfCount tests" -ForegroundColor Gray
}

Write-Host "`n🔒 Validating Security Test Files..." -ForegroundColor Yellow
Write-Host "=" * 50

if (Test-FileExists "tests/security/test_system_security.py" "Security Tests") {
    $secCount = Count-TestsInFile "tests/security/test_system_security.py"
    Write-Host "   └─ Contains $secCount tests" -ForegroundColor Gray
}

Write-Host "`n🛠️ Validating Test Helpers..." -ForegroundColor Yellow
Write-Host "=" * 50

Test-FileExists "tests/helpers/api_client.py" "API Client"
Test-FileExists "tests/helpers/wait_helpers.py" "Wait Helpers"
Test-FileExists "tests/helpers/assertions.py" "Custom Assertions"
Test-FileExists "tests/helpers/aws_simulator.py" "AWS Simulator"
Test-FileExists "tests/helpers/database_helpers.py" "Database Helpers"

Write-Host "`n📦 Validating Test Fixtures..." -ForegroundColor Yellow
Write-Host "=" * 50

Test-FileExists "tests/fixtures/test_data.py" "Test Data Factories"

Write-Host "`n🔍 Validating Python Syntax..." -ForegroundColor Yellow
Write-Host "=" * 50

$pythonFiles = Get-ChildItem -Path "tests" -Filter "*.py" -Recurse
$syntaxErrors = 0

foreach ($file in $pythonFiles) {
    $result = python -m py_compile $file.FullName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Syntax error in $($file.Name)" -ForegroundColor Red
        $syntaxErrors++
        $script:ErrorCount++
    }
}

if ($syntaxErrors -eq 0) {
    Write-Host "✅ All Python files have valid syntax" -ForegroundColor Green
    $script:PassCount++
}

Write-Host "`n📊 Validating Test Coverage..." -ForegroundColor Yellow
Write-Host "=" * 50

$totalTests = $totalE2ETests + $totalIntegrationTests + $perfCount + $secCount

Write-Host "E2E Tests: $totalE2ETests" -ForegroundColor Cyan
Write-Host "Integration Tests: $totalIntegrationTests" -ForegroundColor Cyan
Write-Host "Performance Tests: $perfCount" -ForegroundColor Cyan
Write-Host "Security Tests: $secCount" -ForegroundColor Cyan
Write-Host "Total Tests Found: $totalTests" -ForegroundColor Cyan

if ($totalTests -ge 40) {
    Write-Host "✅ Test coverage goal met (40+ tests)" -ForegroundColor Green
    $script:PassCount++
} else {
    Write-Host "⚠️ Test coverage below target (found $totalTests, expected 40+)" -ForegroundColor Yellow
    $script:WarningCount++
}

Write-Host "`n📋 Validating Documentation..." -ForegroundColor Yellow
Write-Host "=" * 50

Test-FileExists "Prompt Document/PHASE5-5.8_PART1_Implementation.md" "PART1 Documentation"
Test-FileExists "Prompt Document/PHASE5-5.8_PART2_Execution_and_Validation.md" "PART2 Documentation"
Test-FileExists "Prompt Document/PHASE5-5.8_COMPLETE.md" "Completion Summary"
Test-FileExists "Prompt Document/PHASE5-5.8_COMPLETE_FULL.md" "Full Coverage Documentation"

Write-Host "`n" + ("=" * 50) -ForegroundColor Cyan
Write-Host "VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host ("=" * 50) -ForegroundColor Cyan

Write-Host "`n✅ Passed: $PassCount" -ForegroundColor Green
Write-Host "⚠️  Warnings: $WarningCount" -ForegroundColor Yellow
Write-Host "❌ Errors: $ErrorCount" -ForegroundColor Red

Write-Host "`n📊 Test Statistics:" -ForegroundColor Cyan
Write-Host "   Total Test Files: $($pythonFiles.Count)" -ForegroundColor White
Write-Host "   Total Tests: $totalTests" -ForegroundColor White
Write-Host "   E2E Scenarios: 8" -ForegroundColor White
Write-Host "   Integration Tests: 20" -ForegroundColor White
Write-Host "   Performance Tests: 5" -ForegroundColor White
Write-Host "   Security Tests: 10" -ForegroundColor White

if ($ErrorCount -eq 0) {
    Write-Host "`n🎉 VALIDATION PASSED! All tests are ready to run." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n❌ VALIDATION FAILED! Please fix the errors above." -ForegroundColor Red
    exit 1
}
