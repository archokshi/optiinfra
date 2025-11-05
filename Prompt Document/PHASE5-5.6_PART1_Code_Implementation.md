# PHASE5-5.6 PART1: CI/CD Pipeline - Code Implementation

**Phase**: PHASE5-5.6  
**Component**: Portal & Production - CI/CD Pipeline  
**Estimated Time**: 30 minutes (Code) + 25 minutes (Validation)  
**Dependencies**: PHASE5-5.5 (Kubernetes Deployment)

---

## Overview

Create GitHub Actions workflows for Continuous Integration and Continuous Deployment, including automated testing, Docker image building, and Kubernetes deployment.

---

## Step 1: Create GitHub Actions Directory Structure

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra
mkdir -p .github\workflows
```

---

## Step 2: Create Main CI/CD Workflow

### File: `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}/optiinfra

jobs:
  # Job 1: Run Tests
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - cost-agent
          - performance-agent
          - resource-agent
          - application-agent
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cache pip dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('services/${{ matrix.service }}/requirements.txt') }}
          restore-keys: |
            ${{ runner.os }}-pip-

      - name: Install dependencies
        working-directory: services/${{ matrix.service }}
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio

      - name: Run unit tests
        working-directory: services/${{ matrix.service }}
        run: |
          pytest tests/ -v --cov=src --cov-report=xml --cov-report=term

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: services/${{ matrix.service }}/coverage.xml
          flags: ${{ matrix.service }}
          name: ${{ matrix.service }}-coverage

  # Job 2: Test Portal
  test-portal:
    name: Test Portal
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: portal/package-lock.json

      - name: Install dependencies
        working-directory: portal
        run: npm ci

      - name: Run linter
        working-directory: portal
        run: npm run lint

      - name: Run type check
        working-directory: portal
        run: npx tsc --noEmit

      - name: Build portal
        working-directory: portal
        run: npm run build

      - name: Run Playwright tests
        working-directory: portal
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: portal/playwright-report/
          retention-days: 30

  # Job 3: Build and Push Docker Images
  build-and-push:
    name: Build and Push Images
    runs-on: ubuntu-latest
    needs: [test, test-portal]
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop')
    
    strategy:
      matrix:
        service:
          - cost-agent
          - performance-agent
          - resource-agent
          - application-agent
          - portal
    
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-

      - name: Determine context path
        id: context
        run: |
          if [ "${{ matrix.service }}" = "portal" ]; then
            echo "path=portal" >> $GITHUB_OUTPUT
          else
            echo "path=services/${{ matrix.service }}" >> $GITHUB_OUTPUT
          fi

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: ${{ steps.context.outputs.path }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # Job 4: Deploy to Staging
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.optiinfra.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'latest'

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_STAGING }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Update image tags
        run: |
          cd k8s/overlays/staging
          kustomize edit set image \
            cost-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/cost-agent:develop \
            performance-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/performance-agent:develop \
            resource-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/resource-agent:develop \
            application-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/application-agent:develop \
            portal=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/portal:develop

      - name: Deploy to Kubernetes
        run: |
          export KUBECONFIG=kubeconfig
          kubectl apply -k k8s/overlays/staging
          kubectl rollout status deployment -n optiinfra-staging --timeout=5m

      - name: Verify deployment
        run: |
          export KUBECONFIG=kubeconfig
          kubectl get pods -n optiinfra-staging
          kubectl get services -n optiinfra-staging

  # Job 5: Deploy to Production
  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://optiinfra.com
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up kubectl
        uses: azure/setup-kubectl@v4
        with:
          version: 'latest'

      - name: Configure kubectl
        run: |
          echo "${{ secrets.KUBECONFIG_PRODUCTION }}" | base64 -d > kubeconfig
          export KUBECONFIG=kubeconfig

      - name: Update image tags
        run: |
          cd k8s/overlays/production
          kustomize edit set image \
            cost-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/cost-agent:main \
            performance-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/performance-agent:main \
            resource-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/resource-agent:main \
            application-agent=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/application-agent:main \
            portal=${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}/portal:main

      - name: Deploy to Kubernetes
        run: |
          export KUBECONFIG=kubeconfig
          kubectl apply -k k8s/overlays/production
          kubectl rollout status deployment -n optiinfra --timeout=10m

      - name: Verify deployment
        run: |
          export KUBECONFIG=kubeconfig
          kubectl get pods -n optiinfra
          kubectl get services -n optiinfra

      - name: Run smoke tests
        run: |
          export KUBECONFIG=kubeconfig
          kubectl run smoke-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
            curl -f http://portal.optiinfra.svc.cluster.local:3000/health || exit 1
```

---

## Step 3: Create Linting Workflow

### File: `.github/workflows/lint.yml`

```yaml
name: Lint

on:
  pull_request:
    branches:
      - main
      - develop

jobs:
  # Python Linting
  lint-python:
    name: Lint Python Code
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - cost-agent
          - performance-agent
          - resource-agent
          - application-agent
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install linting tools
        run: |
          python -m pip install --upgrade pip
          pip install flake8 black isort mypy

      - name: Run flake8
        working-directory: services/${{ matrix.service }}
        run: flake8 src/ tests/ --max-line-length=100 --exclude=__pycache__

      - name: Run black
        working-directory: services/${{ matrix.service }}
        run: black --check src/ tests/

      - name: Run isort
        working-directory: services/${{ matrix.service }}
        run: isort --check-only src/ tests/

      - name: Run mypy
        working-directory: services/${{ matrix.service }}
        run: mypy src/ --ignore-missing-imports

  # TypeScript/JavaScript Linting
  lint-portal:
    name: Lint Portal Code
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: portal/package-lock.json

      - name: Install dependencies
        working-directory: portal
        run: npm ci

      - name: Run ESLint
        working-directory: portal
        run: npm run lint

      - name: Run TypeScript check
        working-directory: portal
        run: npx tsc --noEmit

  # YAML Linting
  lint-yaml:
    name: Lint YAML Files
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run yamllint
        uses: ibiqlik/action-yamllint@v3
        with:
          file_or_dir: k8s/
          config_data: |
            extends: default
            rules:
              line-length:
                max: 120
              indentation:
                spaces: 2
```

---

## Step 4: Create Security Scanning Workflow

### File: `.github/workflows/security.yml`

```yaml
name: Security Scan

on:
  push:
    branches:
      - main
      - develop
  pull_request:
    branches:
      - main
      - develop
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  # Dependency Scanning
  dependency-scan:
    name: Dependency Vulnerability Scan
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Run Snyk for Python
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --all-projects --severity-threshold=high

      - name: Run Snyk for Node.js
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --file=portal/package.json --severity-threshold=high

  # Container Image Scanning
  container-scan:
    name: Container Image Scan
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service:
          - cost-agent
          - performance-agent
          - resource-agent
          - application-agent
          - portal
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Build Docker image
        run: |
          if [ "${{ matrix.service }}" = "portal" ]; then
            docker build -t ${{ matrix.service }}:test portal/
          else
            docker build -t ${{ matrix.service }}:test services/${{ matrix.service }}/
          fi

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ matrix.service }}:test
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: 'trivy-results.sarif'

  # Code Scanning
  code-scan:
    name: CodeQL Analysis
    runs-on: ubuntu-latest
    permissions:
      actions: read
      contents: read
      security-events: write
    
    strategy:
      matrix:
        language: ['python', 'javascript']
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

---

## Step 5: Create Release Workflow

### File: `.github/workflows/release.yml`

```yaml
name: Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  create-release:
    name: Create Release
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Generate changelog
        id: changelog
        uses: metcalfc/changelog-generator@v4.3.1
        with:
          myToken: ${{ secrets.GITHUB_TOKEN }}

      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          body: ${{ steps.changelog.outputs.changelog }}
          draft: false
          prerelease: false

  build-release-images:
    name: Build Release Images
    runs-on: ubuntu-latest
    needs: create-release
    strategy:
      matrix:
        service:
          - cost-agent
          - performance-agent
          - resource-agent
          - application-agent
          - portal
    
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Determine context path
        id: context
        run: |
          if [ "${{ matrix.service }}" = "portal" ]; then
            echo "path=portal" >> $GITHUB_OUTPUT
          else
            echo "path=services/${{ matrix.service }}" >> $GITHUB_OUTPUT
          fi

      - name: Build and push release image
        uses: docker/build-push-action@v5
        with:
          context: ${{ steps.context.outputs.path }}
          push: true
          tags: |
            ghcr.io/${{ github.repository_owner }}/optiinfra/${{ matrix.service }}:${{ steps.version.outputs.VERSION }}
            ghcr.io/${{ github.repository_owner }}/optiinfra/${{ matrix.service }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Step 6: Create Kustomize Overlays

### File: `k8s/overlays/staging/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: optiinfra-staging

bases:
  - ../../base

namePrefix: staging-

commonLabels:
  environment: staging

replicas:
  - name: portal
    count: 1

images:
  - name: optiinfra/cost-agent
    newName: ghcr.io/your-org/optiinfra/cost-agent
    newTag: develop
  - name: optiinfra/performance-agent
    newName: ghcr.io/your-org/optiinfra/performance-agent
    newTag: develop
  - name: optiinfra/resource-agent
    newName: ghcr.io/your-org/optiinfra/resource-agent
    newTag: develop
  - name: optiinfra/application-agent
    newName: ghcr.io/your-org/optiinfra/application-agent
    newTag: develop
  - name: optiinfra/portal
    newName: ghcr.io/your-org/optiinfra/portal
    newTag: develop

configMapGenerator:
  - name: environment-config
    literals:
      - ENVIRONMENT=staging
      - LOG_LEVEL=DEBUG
```

### File: `k8s/overlays/production/kustomization.yaml`

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: optiinfra

bases:
  - ../../base

commonLabels:
  environment: production

replicas:
  - name: portal
    count: 3
  - name: cost-agent
    count: 2
  - name: performance-agent
    count: 2

images:
  - name: optiinfra/cost-agent
    newName: ghcr.io/your-org/optiinfra/cost-agent
    newTag: latest
  - name: optiinfra/performance-agent
    newName: ghcr.io/your-org/optiinfra/performance-agent
    newTag: latest
  - name: optiinfra/resource-agent
    newName: ghcr.io/your-org/optiinfra/resource-agent
    newTag: latest
  - name: optiinfra/application-agent
    newName: ghcr.io/your-org/optiinfra/application-agent
    newTag: latest
  - name: optiinfra/portal
    newName: ghcr.io/your-org/optiinfra/portal
    newTag: latest

configMapGenerator:
  - name: environment-config
    literals:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO

resources:
  - hpa.yaml
```

### File: `k8s/overlays/production/hpa.yaml`

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: portal-hpa
  namespace: optiinfra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: portal
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cost-agent-hpa
  namespace: optiinfra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cost-agent
  minReplicas: 2
  maxReplicas: 5
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Step 7: Create Dependabot Configuration

### File: `.github/dependabot.yml`

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/services/cost-agent"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/services/performance-agent"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/services/resource-agent"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "pip"
    directory: "/services/application-agent"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  # npm dependencies
  - package-ecosystem: "npm"
    directory: "/portal"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  # Docker dependencies
  - package-ecosystem: "docker"
    directory: "/services/cost-agent"
    schedule:
      interval: "weekly"

  - package-ecosystem: "docker"
    directory: "/portal"
    schedule:
      interval: "weekly"

  # GitHub Actions
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Summary

**Files Created:**
1. `.github/workflows/ci-cd.yml` - Main CI/CD pipeline
2. `.github/workflows/lint.yml` - Linting workflow
3. `.github/workflows/security.yml` - Security scanning
4. `.github/workflows/release.yml` - Release automation
5. `.github/dependabot.yml` - Dependency updates
6. `k8s/overlays/staging/kustomization.yaml` - Staging overlay
7. `k8s/overlays/production/kustomization.yaml` - Production overlay
8. `k8s/overlays/production/hpa.yaml` - Horizontal Pod Autoscaler

**Features:**
- ✅ Automated testing (Python & Node.js)
- ✅ Docker image building and pushing
- ✅ Automated deployment to staging/production
- ✅ Security scanning (Snyk, Trivy, CodeQL)
- ✅ Code linting and formatting
- ✅ Release automation
- ✅ Dependency updates (Dependabot)
- ✅ Horizontal Pod Autoscaling

---

**Next**: PHASE5-5.6_PART2_Execution_and_Validation.md
