# PHASE5-5.6 PART2: CI/CD Pipeline - Execution and Validation

**Phase**: PHASE5-5.6  
**Component**: Portal & Production - CI/CD Pipeline  
**Estimated Time**: 25 minutes  
**Prerequisites**: PHASE5-5.6_PART1 completed, GitHub repository, Docker Hub or GitHub Container Registry access

---

## Prerequisites Check

### Required Tools

```bash
# Check Git
git --version

# Check GitHub CLI (optional but recommended)
gh --version

# Check Docker
docker --version

# Check kubectl
kubectl version --client
```

**Expected**: All tools installed and accessible

---

## Execution Steps

### Step 1: Create GitHub Actions Directory

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Create .github/workflows directory
mkdir .github\workflows
```

---

### Step 2: Create All Workflow Files

Create the following files from PART1:

1. ✅ `.github/workflows/ci-cd.yml` - Main CI/CD pipeline
2. ✅ `.github/workflows/lint.yml` - Linting workflow
3. ✅ `.github/workflows/security.yml` - Security scanning
4. ✅ `.github/workflows/release.yml` - Release automation
5. ✅ `.github/dependabot.yml` - Dependency updates

---

### Step 3: Create Kustomize Overlays

Create overlay directories and files:

```bash
# Create overlay directories
mkdir k8s\overlays\staging
mkdir k8s\overlays\production

# Create kustomization files
# - k8s/overlays/staging/kustomization.yaml
# - k8s/overlays/production/kustomization.yaml
# - k8s/overlays/production/hpa.yaml
```

---

### Step 4: Configure GitHub Repository Secrets

#### Required Secrets:

1. **GITHUB_TOKEN** (automatically provided by GitHub Actions)
2. **KUBECONFIG_STAGING** (base64-encoded kubeconfig for staging cluster)
3. **KUBECONFIG_PRODUCTION** (base64-encoded kubeconfig for production cluster)
4. **SNYK_TOKEN** (optional, for security scanning)

#### How to Add Secrets:

```bash
# Using GitHub CLI
gh secret set KUBECONFIG_STAGING < staging-kubeconfig.yaml

# Or via GitHub Web UI:
# 1. Go to repository Settings
# 2. Click "Secrets and variables" > "Actions"
# 3. Click "New repository secret"
# 4. Add name and value
```

#### Generate base64-encoded kubeconfig:

```bash
# Linux/Mac
cat ~/.kube/config | base64

# Windows PowerShell
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes((Get-Content ~/.kube/config -Raw)))
```

---

### Step 5: Initialize Git Repository (if not already done)

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Initialize git (if needed)
git init

# Add remote
git remote add origin https://github.com/your-username/optiinfra.git

# Create .gitignore if not exists
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "node_modules/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".pytest_cache/" >> .gitignore
echo "coverage.xml" >> .gitignore
echo ".coverage" >> .gitignore
```

---

### Step 6: Commit and Push Workflows

```bash
# Add all workflow files
git add .github/

# Add kustomize overlays
git add k8s/overlays/

# Commit
git commit -m "Add CI/CD workflows and deployment overlays"

# Push to main branch
git push origin main
```

---

### Step 7: Verify Workflows are Triggered

```bash
# Check workflow runs using GitHub CLI
gh run list

# Watch a specific workflow run
gh run watch

# Or check on GitHub web UI:
# https://github.com/your-username/optiinfra/actions
```

---

## Validation Steps

### Test 1: Verify Workflow Files Exist

```bash
# Check all workflow files are present
ls .github\workflows\

# Expected files:
# - ci-cd.yml
# - lint.yml
# - security.yml
# - release.yml
```

**✅ Pass Criteria**: All 4 workflow files exist

---

### Test 2: Validate Workflow Syntax

```bash
# Using GitHub CLI to validate
gh workflow list

# Check for syntax errors
gh workflow view ci-cd.yml
gh workflow view lint.yml
gh workflow view security.yml
gh workflow view release.yml
```

**✅ Pass Criteria**: All workflows listed without errors

---

### Test 3: Verify Kustomize Overlays

```bash
# Validate staging overlay
kubectl kustomize k8s/overlays/staging

# Validate production overlay
kubectl kustomize k8s/overlays/production
```

**✅ Pass Criteria**: Kustomize generates valid manifests

---

### Test 4: Test CI Pipeline (Manual Trigger)

```bash
# Trigger workflow manually using GitHub CLI
gh workflow run ci-cd.yml

# Check status
gh run list --workflow=ci-cd.yml

# View logs
gh run view --log
```

**✅ Pass Criteria**: Workflow runs successfully

---

### Test 5: Test Linting Workflow

```bash
# Create a test branch
git checkout -b test-lint

# Make a small change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test lint workflow"
git push origin test-lint

# Create pull request
gh pr create --title "Test Lint" --body "Testing lint workflow"

# Check if lint workflow runs
gh run list --workflow=lint.yml
```

**✅ Pass Criteria**: Lint workflow runs on PR

---

### Test 6: Verify Docker Image Build

```bash
# Check if images are being built
gh run list --workflow=ci-cd.yml

# View build logs
gh run view <run-id> --log

# Check GitHub Container Registry
# https://github.com/your-username?tab=packages
```

**✅ Pass Criteria**: Docker images built and pushed successfully

---

### Test 7: Test Dependabot Configuration

```bash
# Check if Dependabot is enabled
gh api repos/:owner/:repo/vulnerability-alerts

# View Dependabot alerts
gh api repos/:owner/:repo/dependabot/alerts
```

**✅ Pass Criteria**: Dependabot configuration recognized

---

### Test 8: Verify Deployment to Staging (if cluster available)

```bash
# Check deployment status
kubectl get deployments -n optiinfra-staging

# Check pods
kubectl get pods -n optiinfra-staging

# Check services
kubectl get services -n optiinfra-staging
```

**✅ Pass Criteria**: All deployments running in staging

---

### Test 9: Test Release Workflow

```bash
# Create a release tag
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0

# Check if release workflow runs
gh run list --workflow=release.yml

# Verify release created
gh release list
```

**✅ Pass Criteria**: Release created with tagged images

---

### Test 10: Verify Security Scanning

```bash
# Check security workflow runs
gh run list --workflow=security.yml

# View security alerts
gh api repos/:owner/:repo/code-scanning/alerts

# Check Dependabot security updates
gh api repos/:owner/:repo/dependabot/alerts
```

**✅ Pass Criteria**: Security scans complete without critical issues

---

## Troubleshooting

### Issue: Workflow not triggering

**Check**:
```bash
# Verify workflow syntax
gh workflow view ci-cd.yml

# Check repository permissions
gh api repos/:owner/:repo --jq '.permissions'
```

**Common Causes**:
- Syntax errors in YAML
- Branch protection rules
- Insufficient permissions

---

### Issue: Docker build failing

**Check**:
```bash
# View build logs
gh run view <run-id> --log

# Test build locally
docker build -t test services/cost-agent/
```

**Common Causes**:
- Missing dependencies in requirements.txt
- Dockerfile syntax errors
- Build context issues

---

### Issue: Deployment failing

**Check**:
```bash
# Check secrets are set
gh secret list

# Verify kubeconfig
echo $KUBECONFIG_STAGING | base64 -d | kubectl --kubeconfig=- cluster-info
```

**Common Causes**:
- Invalid kubeconfig
- Insufficient cluster permissions
- Image pull errors

---

### Issue: Tests failing

**Check**:
```bash
# Run tests locally
cd services/cost-agent
pytest tests/ -v

# Check test logs in workflow
gh run view <run-id> --log
```

**Common Causes**:
- Missing test dependencies
- Environment variable issues
- Test database not available

---

## Cleanup

```bash
# Delete test branch
git branch -d test-lint
git push origin --delete test-lint

# Close test PR
gh pr close <pr-number>

# Delete test workflow runs (optional)
# Note: Workflow runs are automatically deleted after 90 days
```

---

## Verification Checklist

- [ ] All workflow files created (4 files)
- [ ] Dependabot configuration created
- [ ] Kustomize overlays created (staging & production)
- [ ] GitHub repository secrets configured
- [ ] Workflows validated (no syntax errors)
- [ ] CI pipeline runs successfully
- [ ] Linting workflow runs on PR
- [ ] Docker images built and pushed
- [ ] Security scanning configured
- [ ] Dependabot enabled
- [ ] Release workflow tested
- [ ] Deployment to staging verified (if cluster available)
- [ ] HPA configured for production

---

## Expected File Structure

```
optiinfra/
├── .github/
│   ├── workflows/
│   │   ├── ci-cd.yml              ✅
│   │   ├── lint.yml               ✅
│   │   ├── security.yml           ✅
│   │   └── release.yml            ✅
│   └── dependabot.yml             ✅
├── k8s/
│   ├── base/
│   │   └── ... (from PHASE5-5.5)
│   └── overlays/
│       ├── staging/
│       │   └── kustomization.yaml ✅
│       └── production/
│           ├── kustomization.yaml ✅
│           └── hpa.yaml           ✅
└── ...
```

---

## Success Criteria

✅ **CI/CD Pipeline Working**
- Workflows trigger on push/PR
- Tests run automatically
- Docker images built and pushed
- Deployments automated

✅ **Code Quality**
- Linting enforced on PRs
- Type checking enabled
- Code coverage tracked

✅ **Security**
- Dependency scanning active
- Container scanning enabled
- CodeQL analysis running
- Security alerts monitored

✅ **Automation**
- Dependabot updates dependencies
- Releases automated with tags
- Deployments to staging/production automated

---

## Performance Metrics

- **Build Time**: < 10 minutes per service
- **Test Time**: < 5 minutes per service
- **Deployment Time**: < 5 minutes
- **Total Pipeline Time**: < 20 minutes

---

## CI/CD Pipeline Flow

```
┌─────────────────────────────────────────────────────────┐
│                    Push to Branch                       │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Run Tests (Parallel)                       │
│  ┌──────────┬──────────┬──────────┬──────────┐        │
│  │ Cost     │ Perf     │ Resource │ App      │        │
│  │ Agent    │ Agent    │ Agent    │ Agent    │        │
│  └──────────┴──────────┴──────────┴──────────┘        │
│              + Portal Tests                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│           Build & Push Docker Images                    │
│              (if tests pass)                            │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│              Deploy to Environment                      │
│  ┌─────────────────┬─────────────────┐                │
│  │ develop branch  │  main branch    │                │
│  │ → Staging       │  → Production   │                │
│  └─────────────────┴─────────────────┘                │
└─────────────────────────────────────────────────────────┘
```

---

## GitHub Actions Features Used

- ✅ Matrix builds (parallel testing)
- ✅ Caching (pip, npm, Docker layers)
- ✅ Artifacts (test reports, coverage)
- ✅ Environments (staging, production)
- ✅ Secrets management
- ✅ Conditional execution
- ✅ Manual approvals (production)
- ✅ Scheduled workflows (security scans)

---

## Next Steps

After validation:
1. ✅ Mark PHASE5-5.6 as complete
2. 📝 Create PHASE5-5.6_COMPLETE.md
3. 🚀 Proceed to PHASE5-5.7 API Security

---

## Additional Resources

### GitHub Actions Documentation
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflow-syntax-for-github-actions)
- [Encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)

### Kustomize Documentation
- [Kustomize overlays](https://kubectl.docs.kubernetes.io/references/kustomize/glossary/#overlay)
- [Image transformers](https://kubectl.docs.kubernetes.io/references/kustomize/kustomization/images/)

### Security Tools
- [Snyk](https://snyk.io/docs/)
- [Trivy](https://aquasecurity.github.io/trivy/)
- [CodeQL](https://codeql.github.com/docs/)

---

**Status**: Ready for execution ✅
