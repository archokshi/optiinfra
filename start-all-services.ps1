# Start All OptiInfra Services
# Launches OptiInfra services for local testing.

param(
    [switch]$IncludeOptional
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Starting OptiInfra Services" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

#------------------------------------------------------------------------------
# Verify infrastructure dependencies
#------------------------------------------------------------------------------
Write-Host "Checking supporting services (Docker containers)..." -ForegroundColor Yellow
$containersOutput = docker ps --format "{{.Names}}" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is not running or not accessible. Start Docker Desktop and re-run this script." -ForegroundColor Red
    exit 1
}

$containers = $containersOutput -split "`r?`n" | Where-Object { $_ -ne "" }
$requiredContainers = @(
    @{ Name = "optiinfra-postgres"; Label = "PostgreSQL" },
    @{ Name = "optiinfra-redis"; Label = "Redis" },
    @{ Name = "optiinfra-clickhouse"; Label = "ClickHouse" },
    @{ Name = "optiinfra-qdrant"; Label = "Qdrant" }
)

$missing = $requiredContainers | Where-Object { $containers -notcontains $_.Name }

if ($missing.Count -gt 0) {
    Write-Host "Required databases are not running:" -ForegroundColor Red
    foreach ($item in $missing) {
        Write-Host ("  - {0}" -f $item.Label) -ForegroundColor Red
    }
    Write-Host "`nStart the stack with: docker-compose up -d`n" -ForegroundColor Yellow
    exit 1
}

Write-Host "All database containers are running.`n" -ForegroundColor Green

#------------------------------------------------------------------------------
# Helper to launch an agent
#------------------------------------------------------------------------------
function Start-ServiceInstance {
    param(
        [string]$Name,
        [string]$RelativePath,
        [string]$Command,
        [int]$Port
    )

    $servicePath = Join-Path $repoRoot $RelativePath

    if (-not (Test-Path $servicePath)) {
        Write-Host "Unable to find $Name at $servicePath" -ForegroundColor Red
        return
    }

    if ($Port -gt 0) {
        Write-Host ("Starting {0} (Port {1})..." -f $Name, $Port) -ForegroundColor Yellow
    } else {
        Write-Host ("Starting {0}..." -f $Name) -ForegroundColor Yellow
    }

    $arguments = @("-NoExit", "-Command", $Command)
    Start-Process powershell -WorkingDirectory $servicePath -ArgumentList $arguments | Out-Null

    Start-Sleep -Seconds 2
}

$agents = @(
    @{ Name = "Cost Agent"; RelativePath = "services\cost-agent"; Command = "python -m uvicorn src.main:app --host 0.0.0.0 --port 8001"; Port = 8001 },
    @{ Name = "Performance Agent"; RelativePath = "services\performance-agent"; Command = "python -m uvicorn src.main:app --host 0.0.0.0 --port 8002"; Port = 8002 },
    @{ Name = "Resource Agent"; RelativePath = "services\resource-agent"; Command = "python -m uvicorn src.main:app --host 0.0.0.0 --port 8003"; Port = 8003 },
    @{ Name = "Application Agent"; RelativePath = "services\application-agent"; Command = "python -m uvicorn src.main:app --host 0.0.0.0 --port 8004"; Port = 8004 }
)

foreach ($agent in $agents) {
    Start-ServiceInstance -Name $agent.Name -RelativePath $agent.RelativePath -Command $agent.Command -Port $agent.Port
}

if ($IncludeOptional) {
    if (Get-Command go -ErrorAction SilentlyContinue) {
        $orchestrator = @{
            Name = "Orchestrator"
            RelativePath = "services\orchestrator"
            Command = "go run ./cmd/orchestrator"
            Port = 8080
        }
        Start-ServiceInstance @orchestrator
    } else {
        Write-Host "Skipping Orchestrator (Go toolchain not found in PATH)." -ForegroundColor DarkYellow
    }

    if (Get-Command npm -ErrorAction SilentlyContinue) {
        $portal = @{
            Name = "Portal"
            RelativePath = "portal"
            Command = "npm run dev -- --port 3001"
            Port = 3001
        }
        Start-ServiceInstance @portal
    } else {
        Write-Host "Skipping Portal (npm not found in PATH)." -ForegroundColor DarkYellow
    }
}

Write-Host "`nAll services started!" -ForegroundColor Green
Write-Host "`nServices running on:" -ForegroundColor Cyan
Write-Host "  - Cost Agent:         http://localhost:8001" -ForegroundColor White
Write-Host "  - Performance Agent:  http://localhost:8002" -ForegroundColor White
Write-Host "  - Resource Agent:     http://localhost:8003" -ForegroundColor White
Write-Host "  - Application Agent:  http://localhost:8004" -ForegroundColor White

Write-Host "`nWait ~30 seconds for services to warm up, then run tests with:" -ForegroundColor Yellow
Write-Host "  python -m pytest tests/ -v" -ForegroundColor White
Write-Host "`nPress Ctrl+C in each window to stop a service." -ForegroundColor White
