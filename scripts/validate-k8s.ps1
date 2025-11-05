# PHASE5-5.5 Kubernetes Validation Script
# Validates K8s manifests and Docker builds

Write-Host "=== OptiInfra Kubernetes Validation ===" -ForegroundColor Cyan
Write-Host ""

$projectRoot = "C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra"
$errors = 0

# Test 1: Check if kubectl is installed
Write-Host "[1/8] Checking kubectl..." -ForegroundColor Yellow
try {
    $kubectlVersion = kubectl version --client 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ kubectl is installed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ kubectl not found" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ kubectl not found" -ForegroundColor Red
    $errors++
}

# Test 2: Check if Docker is installed
Write-Host "[2/8] Checking Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Docker is installed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Docker not found" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Docker not found" -ForegroundColor Red
    $errors++
}

# Test 3: Validate Kubernetes manifests (dry-run)
Write-Host "[3/8] Validating Kubernetes manifests..." -ForegroundColor Yellow
Set-Location $projectRoot
try {
    $dryRun = kubectl apply -k k8s/base/ --dry-run=client 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ All manifests are valid" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Manifest validation failed" -ForegroundColor Red
        Write-Host "  Error: $dryRun" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Manifest validation failed" -ForegroundColor Red
    $errors++
}

# Test 4: Check Dockerfile existence
Write-Host "[4/8] Checking Dockerfiles..." -ForegroundColor Yellow
$dockerfiles = @(
    "services\cost-agent\Dockerfile",
    "services\performance-agent\Dockerfile",
    "services\resource-agent\Dockerfile",
    "services\application-agent\Dockerfile",
    "portal\Dockerfile"
)

$missingDockerfiles = 0
foreach ($dockerfile in $dockerfiles) {
    $path = Join-Path $projectRoot $dockerfile
    if (Test-Path $path) {
        Write-Host "  ✓ $dockerfile exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $dockerfile missing" -ForegroundColor Red
        $missingDockerfiles++
    }
}

if ($missingDockerfiles -eq 0) {
    Write-Host "  ✓ All Dockerfiles present" -ForegroundColor Green
} else {
    $errors++
}

# Test 5: Check K8s manifest files
Write-Host "[5/8] Checking K8s manifest files..." -ForegroundColor Yellow
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

$missingManifests = 0
foreach ($manifest in $manifests) {
    $path = Join-Path $projectRoot $manifest
    if (Test-Path $path) {
        Write-Host "  ✓ $manifest exists" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $manifest missing" -ForegroundColor Red
        $missingManifests++
    }
}

if ($missingManifests -eq 0) {
    Write-Host "  ✓ All manifests present (11 files)" -ForegroundColor Green
} else {
    $errors++
}

# Test 6: Test Docker build for Cost Agent
Write-Host "[6/8] Testing Docker build (Cost Agent)..." -ForegroundColor Yellow
Set-Location "$projectRoot\services\cost-agent"
try {
    Write-Host "  Building optiinfra/cost-agent:test..." -ForegroundColor Gray
    $buildOutput = docker build -t optiinfra/cost-agent:test . 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Cost Agent Docker build successful" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Cost Agent Docker build failed" -ForegroundColor Red
        Write-Host "  Error: $buildOutput" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Cost Agent Docker build failed" -ForegroundColor Red
    $errors++
}

# Test 7: Test Docker build for Portal
Write-Host "[7/8] Testing Docker build (Portal)..." -ForegroundColor Yellow
Set-Location "$projectRoot\portal"
try {
    Write-Host "  Building optiinfra/portal:test..." -ForegroundColor Gray
    $buildOutput = docker build -t optiinfra/portal:test . 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Portal Docker build successful" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Portal Docker build failed" -ForegroundColor Red
        Write-Host "  Error: $buildOutput" -ForegroundColor Red
        $errors++
    }
} catch {
    Write-Host "  ✗ Portal Docker build failed" -ForegroundColor Red
    $errors++
}

# Test 8: Check Helm chart
Write-Host "[8/8] Checking Helm chart..." -ForegroundColor Yellow
$helmChart = Join-Path $projectRoot "helm\optiinfra\Chart.yaml"
if (Test-Path $helmChart) {
    Write-Host "  ✓ Helm Chart.yaml exists" -ForegroundColor Green
} else {
    Write-Host "  ✗ Helm Chart.yaml missing" -ForegroundColor Red
    $errors++
}

# Summary
Write-Host ""
Write-Host "=== Validation Summary ===" -ForegroundColor Cyan
if ($errors -eq 0) {
    Write-Host "✓ All validation tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ready for deployment!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Build all Docker images: docker build -t optiinfra/<service>:latest ." -ForegroundColor Gray
    Write-Host "  2. Start Minikube: minikube start --cpus=4 --memory=8192" -ForegroundColor Gray
    Write-Host "  3. Deploy to K8s: kubectl apply -k k8s/base/" -ForegroundColor Gray
    Write-Host "  4. Check status: kubectl get all -n optiinfra" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "✗ $errors validation test(s) failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please fix the errors above before deploying." -ForegroundColor Yellow
    exit 1
}
