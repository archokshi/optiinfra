# Simple K8s Validation Script

Write-Host "=== OptiInfra Kubernetes Validation ===" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra"

# Check kubectl
Write-Host "[1/5] Checking kubectl..." -ForegroundColor Yellow
kubectl version --client 2>$null
if ($?) {
    Write-Host "  OK - kubectl is installed" -ForegroundColor Green
} else {
    Write-Host "  FAIL - kubectl not found" -ForegroundColor Red
}

# Check Docker
Write-Host "[2/5] Checking Docker..." -ForegroundColor Yellow
docker --version 2>$null
if ($?) {
    Write-Host "  OK - Docker is installed" -ForegroundColor Green
} else {
    Write-Host "  FAIL - Docker not found" -ForegroundColor Red
}

# Check manifest files
Write-Host "[3/5] Checking K8s manifest files..." -ForegroundColor Yellow
$manifests = @(
    "k8s\base\namespace.yaml",
    "k8s\base\postgresql.yaml",
    "k8s\base\clickhouse.yaml",
    "k8s\base\qdrant.yaml",
    "k8s\base\cost-agent.yaml",
    "k8s\base\performance-agent.yaml",
    "k8s\base\resource-agent.yaml",
    "k8s\base\application-agent.yaml",
    "k8s\base\portal.yaml",
    "k8s\base\ingress.yaml",
    "k8s\base\kustomization.yaml"
)

$allExist = $true
foreach ($manifest in $manifests) {
    $path = Join-Path $projectRoot $manifest
    if (-not (Test-Path $path)) {
        Write-Host "  MISSING: $manifest" -ForegroundColor Red
        $allExist = $false
    }
}

if ($allExist) {
    Write-Host "  OK - All 11 manifests present" -ForegroundColor Green
}

# Check Dockerfiles
Write-Host "[4/5] Checking Dockerfiles..." -ForegroundColor Yellow
$dockerfiles = @(
    "services\cost-agent\Dockerfile",
    "services\performance-agent\Dockerfile",
    "services\resource-agent\Dockerfile",
    "services\application-agent\Dockerfile",
    "portal\Dockerfile"
)

$allDockerfilesExist = $true
foreach ($dockerfile in $dockerfiles) {
    $path = Join-Path $projectRoot $dockerfile
    if (-not (Test-Path $path)) {
        Write-Host "  MISSING: $dockerfile" -ForegroundColor Red
        $allDockerfilesExist = $false
    }
}

if ($allDockerfilesExist) {
    Write-Host "  OK - All 5 Dockerfiles present" -ForegroundColor Green
}

# Validate manifests with kubectl
Write-Host "[5/5] Validating manifest syntax..." -ForegroundColor Yellow
Set-Location $projectRoot
kubectl apply -k k8s/base/ --dry-run=client 2>$null
if ($?) {
    Write-Host "  OK - All manifests are valid" -ForegroundColor Green
} else {
    Write-Host "  FAIL - Manifest validation failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Validation Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "To deploy locally:" -ForegroundColor Yellow
Write-Host "  1. minikube start --cpus=4 --memory=8192" -ForegroundColor Gray
Write-Host "  2. kubectl apply -k k8s/base/" -ForegroundColor Gray
Write-Host "  3. kubectl get all -n optiinfra" -ForegroundColor Gray
