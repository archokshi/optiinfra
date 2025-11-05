# PHASE5-5.5 PART2: Kubernetes Deployment - Execution and Validation

**Phase**: PHASE5-5.5  
**Component**: Portal & Production - Kubernetes Deployment  
**Estimated Time**: 30 minutes  
**Prerequisites**: PHASE5-5.5_PART1 completed, Docker installed, Kubernetes cluster available

---

## Prerequisites Check

### Required Tools

```bash
# Check Docker
docker --version

# Check Kubernetes (kubectl)
kubectl version --client

# Check Helm (optional)
helm version

# Check Minikube (for local testing)
minikube version
```

**Expected**: All tools installed and accessible

---

## Execution Steps

### Step 1: Create Directory Structure

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Create directories
mkdir k8s\base
mkdir k8s\overlays\dev
mkdir k8s\overlays\prod
mkdir helm\optiinfra\templates
mkdir helm\optiinfra\charts
mkdir scripts
```

---

### Step 2: Create All Kubernetes Manifests

Create the following files from PART1:

1. ✅ `k8s/base/namespace.yaml`
2. ✅ `k8s/base/postgresql.yaml`
3. ✅ `k8s/base/clickhouse.yaml`
4. ✅ `k8s/base/qdrant.yaml`
5. ✅ `k8s/base/cost-agent.yaml`
6. ✅ `k8s/base/performance-agent.yaml`
7. ✅ `k8s/base/resource-agent.yaml`
8. ✅ `k8s/base/application-agent.yaml`
9. ✅ `k8s/base/portal.yaml`
10. ✅ `k8s/base/ingress.yaml`
11. ✅ `k8s/base/kustomization.yaml`

---

### Step 3: Create Helm Chart Files

Create the following files from PART1:

1. ✅ `helm/optiinfra/Chart.yaml`
2. ✅ `helm/optiinfra/values.yaml`

---

### Step 4: Create Dockerfiles for Each Service

#### File: `services/cost-agent/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### File: `services/performance-agent/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

#### File: `services/resource-agent/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 8003

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

#### File: `services/application-agent/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY tests/ ./tests/

# Expose port
EXPOSE 8004

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8004"]
```

#### File: `portal/Dockerfile`

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

# Copy built application
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public

# Expose port
EXPOSE 3000

# Run the application
CMD ["npm", "start"]
```

---

### Step 5: Build Docker Images

```bash
# Navigate to project root
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Build Cost Agent
cd services\cost-agent
docker build -t optiinfra/cost-agent:latest .
cd ..\..

# Build Performance Agent
cd services\performance-agent
docker build -t optiinfra/performance-agent:latest .
cd ..\..

# Build Resource Agent
cd services\resource-agent
docker build -t optiinfra/resource-agent:latest .
cd ..\..

# Build Application Agent
cd services\application-agent
docker build -t optiinfra/application-agent:latest .
cd ..\..

# Build Portal
cd portal
docker build -t optiinfra/portal:latest .
cd ..
```

**Expected Output**: All images built successfully

---

### Step 6: Start Local Kubernetes Cluster (Minikube)

```bash
# Start Minikube
minikube start --cpus=4 --memory=8192

# Enable Ingress addon
minikube addons enable ingress

# Verify cluster is running
kubectl cluster-info
```

**Expected Output**: Kubernetes cluster running

---

### Step 7: Load Docker Images into Minikube

```bash
# Load images into Minikube
minikube image load optiinfra/cost-agent:latest
minikube image load optiinfra/performance-agent:latest
minikube image load optiinfra/resource-agent:latest
minikube image load optiinfra/application-agent:latest
minikube image load optiinfra/portal:latest
```

**Expected Output**: Images loaded successfully

---

### Step 8: Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -k k8s/base/

# Verify namespace created
kubectl get namespace optiinfra
```

**Expected Output**: All resources created

---

### Step 9: Verify Deployments

```bash
# Check all pods
kubectl get pods -n optiinfra

# Check all services
kubectl get services -n optiinfra

# Check all deployments
kubectl get deployments -n optiinfra

# Check ingress
kubectl get ingress -n optiinfra
```

**Expected Output**: All pods running, services created, ingress configured

---

## Validation Steps

### Test 1: Check Namespace

```bash
kubectl get namespace optiinfra
```

**✅ Pass Criteria**: Namespace exists and is Active

---

### Test 2: Check Database Pods

```bash
kubectl get pods -n optiinfra -l app=postgresql
kubectl get pods -n optiinfra -l app=clickhouse
kubectl get pods -n optiinfra -l app=qdrant
```

**✅ Pass Criteria**: All database pods are Running (1/1)

---

### Test 3: Check Agent Pods

```bash
kubectl get pods -n optiinfra -l agent-type=cost
kubectl get pods -n optiinfra -l agent-type=performance
kubectl get pods -n optiinfra -l agent-type=resource
kubectl get pods -n optiinfra -l agent-type=application
```

**✅ Pass Criteria**: All agent pods are Running (1/1)

---

### Test 4: Check Portal Pods

```bash
kubectl get pods -n optiinfra -l app=portal
```

**✅ Pass Criteria**: Portal pods are Running (2/2 replicas)

---

### Test 5: Check Services

```bash
kubectl get services -n optiinfra
```

**Expected Services**:
- postgresql (ClusterIP)
- clickhouse (ClusterIP)
- qdrant (ClusterIP)
- cost-agent (ClusterIP)
- performance-agent (ClusterIP)
- resource-agent (ClusterIP)
- application-agent (ClusterIP)
- portal (LoadBalancer)

**✅ Pass Criteria**: All services created with correct types

---

### Test 6: Check Pod Logs

```bash
# Check Cost Agent logs
kubectl logs -n optiinfra -l app=cost-agent --tail=50

# Check Performance Agent logs
kubectl logs -n optiinfra -l app=performance-agent --tail=50

# Check Portal logs
kubectl logs -n optiinfra -l app=portal --tail=50
```

**✅ Pass Criteria**: No error messages, services started successfully

---

### Test 7: Test Health Endpoints

```bash
# Port forward Cost Agent
kubectl port-forward -n optiinfra svc/cost-agent 8001:8001

# In another terminal, test health endpoint
curl http://localhost:8001/health
```

**Expected Response**: `{"status": "healthy"}`

Repeat for other agents (ports 8002, 8003, 8004)

**✅ Pass Criteria**: All health endpoints return healthy status

---

### Test 8: Test Portal Access

```bash
# Port forward Portal
kubectl port-forward -n optiinfra svc/portal 3000:3000

# Open browser to http://localhost:3000
```

**✅ Pass Criteria**: Portal loads successfully, login page displays

---

### Test 9: Check Resource Usage

```bash
# Check resource usage
kubectl top pods -n optiinfra

# Check resource limits
kubectl describe deployment cost-agent -n optiinfra | grep -A 5 "Limits"
```

**✅ Pass Criteria**: Resource usage within defined limits

---

### Test 10: Test Ingress

```bash
# Get Minikube IP
minikube ip

# Add to hosts file (Windows: C:\Windows\System32\drivers\etc\hosts)
# <minikube-ip> optiinfra.local

# Access via browser
# http://optiinfra.local
```

**✅ Pass Criteria**: Portal accessible via ingress

---

## Troubleshooting

### Issue: Pods not starting

**Check**:
```bash
kubectl describe pod <pod-name> -n optiinfra
kubectl logs <pod-name> -n optiinfra
```

**Common Causes**:
- Image pull errors (check imagePullPolicy)
- Resource constraints
- Configuration errors

---

### Issue: Services not accessible

**Check**:
```bash
kubectl get endpoints -n optiinfra
kubectl describe service <service-name> -n optiinfra
```

**Common Causes**:
- Pod not ready
- Port mismatch
- Selector mismatch

---

### Issue: Database connection errors

**Check**:
```bash
# Test PostgreSQL connection
kubectl exec -it <agent-pod> -n optiinfra -- env | grep DATABASE

# Test from within pod
kubectl exec -it <agent-pod> -n optiinfra -- curl postgresql:5432
```

**Common Causes**:
- Database not ready
- Wrong credentials
- Network policy issues

---

## Cleanup

```bash
# Delete all resources
kubectl delete -k k8s/base/

# Or delete namespace (removes everything)
kubectl delete namespace optiinfra

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

---

## Verification Checklist

- [ ] All Kubernetes manifests created
- [ ] Dockerfiles created for all services
- [ ] Docker images built successfully
- [ ] Minikube cluster started
- [ ] Images loaded into Minikube
- [ ] Namespace created
- [ ] All pods running (8 deployments)
- [ ] All services created (8 services)
- [ ] Ingress configured
- [ ] Health endpoints responding
- [ ] Portal accessible
- [ ] Database connections working
- [ ] Resource limits configured
- [ ] Persistent volumes claimed

---

## Expected File Structure

```
optiinfra/
├── k8s/
│   ├── base/
│   │   ├── namespace.yaml
│   │   ├── postgresql.yaml
│   │   ├── clickhouse.yaml
│   │   ├── qdrant.yaml
│   │   ├── cost-agent.yaml
│   │   ├── performance-agent.yaml
│   │   ├── resource-agent.yaml
│   │   ├── application-agent.yaml
│   │   ├── portal.yaml
│   │   ├── ingress.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── dev/
│       └── prod/
├── helm/
│   └── optiinfra/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
├── services/
│   ├── cost-agent/
│   │   └── Dockerfile
│   ├── performance-agent/
│   │   └── Dockerfile
│   ├── resource-agent/
│   │   └── Dockerfile
│   └── application-agent/
│       └── Dockerfile
└── portal/
    └── Dockerfile
```

---

## Success Criteria

✅ **Kubernetes Deployment Working**
- All pods running
- All services accessible
- Ingress routing correctly
- Health checks passing

✅ **Resource Management**
- Resource limits configured
- Persistent storage working
- ConfigMaps and Secrets applied

✅ **Service Discovery**
- Agents can communicate
- Portal can reach agents
- Databases accessible

✅ **Production Ready**
- Dockerfiles optimized
- Multi-stage builds used
- Security best practices followed

---

## Performance Metrics

- **Deployment Time**: < 5 minutes
- **Pod Startup Time**: < 30 seconds per pod
- **Resource Usage**: Within defined limits
- **Health Check Response**: < 100ms

---

## Next Steps

After validation:
1. ✅ Mark PHASE5-5.5 as complete
2. 📝 Create PHASE5-5.5_COMPLETE.md
3. 🚀 Proceed to PHASE5-5.6 CI/CD Pipeline

---

## Helm Deployment (Alternative)

```bash
# Install using Helm
helm install optiinfra ./helm/optiinfra -n optiinfra --create-namespace

# Upgrade
helm upgrade optiinfra ./helm/optiinfra -n optiinfra

# Uninstall
helm uninstall optiinfra -n optiinfra
```

---

**Status**: Ready for execution ✅
