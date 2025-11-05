# Cost Agent Deployment Guide

**Version**: 1.0.0  
**Last Updated**: 2025-01-23

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Monitoring Setup](#monitoring-setup)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Prerequisites

### System Requirements

- **OS**: Linux, macOS, or Windows with WSL2
- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Kubernetes**: 1.24+ (for K8s deployment)
- **PostgreSQL**: 14+ (for database)
- **Redis**: 6+ (for caching)

### Cloud Provider Credentials

- **AWS**: Access Key ID and Secret Access Key
- **GCP**: Service Account JSON key
- **Azure**: Subscription ID and credentials
- **Vultr**: API Key

### Required Tools

```bash
# Python and pip
python --version  # Should be 3.11+
pip --version

# Docker (optional)
docker --version
docker-compose --version

# Kubernetes (optional)
kubectl version
helm version
```

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/optiinfra/cost-agent.git
cd cost-agent
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your configuration
nano .env
```

**Required Environment Variables**:
```bash
# Application
PORT=8001
ENVIRONMENT=development
LOG_LEVEL=INFO
AGENT_ID=cost-agent-001

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cost_agent
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_DEFAULT_REGION=us-east-1

# GCP
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id

# Azure
AZURE_SUBSCRIPTION_ID=your-subscription-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id

# Vultr
VULTR_API_KEY=your-vultr-api-key

# LLM
GROQ_API_KEY=your-groq-api-key
LLM_MODEL=llama-3.1-70b-versatile
LLM_TEMPERATURE=0.7

# Security
JWT_SECRET_KEY=your-secret-key-here
API_KEY_SALT=your-salt-here
```

---

## Local Development

### 1. Start Dependencies

```bash
# Start PostgreSQL
docker run -d \
  --name cost-agent-postgres \
  -e POSTGRES_DB=cost_agent \
  -e POSTGRES_USER=cost_user \
  -e POSTGRES_PASSWORD=cost_password \
  -p 5432:5432 \
  postgres:14

# Start Redis
docker run -d \
  --name cost-agent-redis \
  -p 6379:6379 \
  redis:6
```

### 2. Initialize Database

```bash
# Run database migrations
python scripts/init_db.py

# Seed initial data (optional)
python scripts/seed_data.py
```

### 3. Run Application

```bash
# Run with Python
python src/main.py

# Or with uvicorn (recommended)
uvicorn src.main:app --reload --port 8001 --host 0.0.0.0

# Or with PowerShell script (Windows)
.\start.ps1
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8001/api/v1/health

# Check API docs
open http://localhost:8001/docs
```

---

## Docker Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t optiinfra/cost-agent:latest .

# Build with specific version
docker build -t optiinfra/cost-agent:1.0.0 .
```

### 2. Run with Docker

```bash
# Run container
docker run -d \
  --name cost-agent \
  -p 8001:8001 \
  --env-file .env \
  optiinfra/cost-agent:latest
```

### 3. Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  cost-agent:
    build: .
    ports:
      - "8001:8001"
    environment:
      - DATABASE_URL=postgresql://cost_user:cost_password@postgres:5432/cost_agent
      - REDIS_URL=redis://redis:6379/0
    env_file:
      - .env
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=cost_agent
      - POSTGRES_USER=cost_user
      - POSTGRES_PASSWORD=cost_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:6
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

**Start with Docker Compose**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f cost-agent

# Stop services
docker-compose down
```

---

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace optiinfra
```

### 2. Create Secrets

```bash
# Create secret for environment variables
kubectl create secret generic cost-agent-secrets \
  --from-env-file=.env \
  --namespace=optiinfra

# Create secret for cloud credentials
kubectl create secret generic cloud-credentials \
  --from-file=gcp-key.json \
  --namespace=optiinfra
```

### 3. Deploy with Helm

**values.yaml**:
```yaml
replicaCount: 3

image:
  repository: optiinfra/cost-agent
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8001

ingress:
  enabled: true
  className: nginx
  hosts:
    - host: cost-agent.optiinfra.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

postgresql:
  enabled: true
  auth:
    database: cost_agent
    username: cost_user
    password: cost_password

redis:
  enabled: true
  auth:
    enabled: false

prometheus:
  enabled: true
  serviceMonitor:
    enabled: true
```

**Install with Helm**:
```bash
# Add Helm repo (if using custom chart)
helm repo add optiinfra https://charts.optiinfra.com
helm repo update

# Install
helm install cost-agent optiinfra/cost-agent \
  --namespace optiinfra \
  --values values.yaml

# Upgrade
helm upgrade cost-agent optiinfra/cost-agent \
  --namespace optiinfra \
  --values values.yaml
```

### 4. Manual Kubernetes Deployment

**deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cost-agent
  namespace: optiinfra
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cost-agent
  template:
    metadata:
      labels:
        app: cost-agent
    spec:
      containers:
      - name: cost-agent
        image: optiinfra/cost-agent:1.0.0
        ports:
        - containerPort: 8001
        envFrom:
        - secretRef:
            name: cost-agent-secrets
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: cost-agent
  namespace: optiinfra
spec:
  selector:
    app: cost-agent
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8001
  type: ClusterIP
```

**Apply manifests**:
```bash
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

---

## Cloud Deployment

### AWS Deployment (ECS)

#### 1. Create ECR Repository

```bash
# Create repository
aws ecr create-repository --repository-name cost-agent

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789012.dkr.ecr.us-east-1.amazonaws.com

# Tag and push image
docker tag optiinfra/cost-agent:latest \
  123456789012.dkr.ecr.us-east-1.amazonaws.com/cost-agent:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/cost-agent:latest
```

#### 2. Create ECS Task Definition

```json
{
  "family": "cost-agent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "cost-agent",
      "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/cost-agent:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "ENVIRONMENT", "value": "production"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789012:secret:cost-agent/db-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/cost-agent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### 3. Create ECS Service

```bash
aws ecs create-service \
  --cluster optiinfra \
  --service-name cost-agent \
  --task-definition cost-agent \
  --desired-count 3 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

---

### GCP Deployment (Cloud Run)

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/cost-agent

# Deploy to Cloud Run
gcloud run deploy cost-agent \
  --image gcr.io/PROJECT_ID/cost-agent \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production \
  --set-secrets DATABASE_URL=cost-agent-db-url:latest \
  --min-instances 1 \
  --max-instances 10 \
  --cpu 1 \
  --memory 1Gi
```

---

### Azure Deployment (Container Instances)

```bash
# Create resource group
az group create --name optiinfra --location eastus

# Create container registry
az acr create --resource-group optiinfra --name optiinfraacr --sku Basic

# Push image
az acr login --name optiinfraacr
docker tag optiinfra/cost-agent:latest optiinfraacr.azurecr.io/cost-agent:latest
docker push optiinfraacr.azurecr.io/cost-agent:latest

# Deploy container
az container create \
  --resource-group optiinfra \
  --name cost-agent \
  --image optiinfraacr.azurecr.io/cost-agent:latest \
  --cpu 1 \
  --memory 1 \
  --registry-login-server optiinfraacr.azurecr.io \
  --registry-username <username> \
  --registry-password <password> \
  --dns-name-label cost-agent \
  --ports 8001 \
  --environment-variables ENVIRONMENT=production
```

---

## Configuration

See [CONFIGURATION.md](CONFIGURATION.md) for complete configuration reference.

---

## Database Setup

### PostgreSQL Setup

```bash
# Create database
createdb cost_agent

# Run migrations
python scripts/migrate.py

# Verify
psql cost_agent -c "\dt"
```

### Database Schema

Key tables:
- `costs` - Cost data
- `recommendations` - Generated recommendations
- `executions` - Execution history
- `feedback` - Learning feedback
- `api_keys` - API key management

---

## Monitoring Setup

### Prometheus Configuration

**prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cost-agent'
    static_configs:
      - targets: ['cost-agent:8001']
    metrics_path: '/metrics'
```

### Grafana Dashboards

Import pre-built dashboards from `monitoring/grafana/dashboards/`.

---

## CI/CD Pipeline

### GitHub Actions

**.github/workflows/deploy.yml**:
```yaml
name: Deploy Cost Agent

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t optiinfra/cost-agent:${{ github.sha }} .
      - name: Push to registry
        run: docker push optiinfra/cost-agent:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/cost-agent \
            cost-agent=optiinfra/cost-agent:${{ github.sha }}
```

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

---

## Support

- **Documentation**: https://docs.optiinfra.com
- **Support**: support@optiinfra.com
- **Status**: https://status.optiinfra.com

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0
