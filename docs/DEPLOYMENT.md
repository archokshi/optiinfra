# Deployment Guide

## Overview

OptiInfra can be deployed to Kubernetes clusters on any cloud provider (AWS, GCP, Azure) or on-premises.

## Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Docker registry access
- Helm 3+ (optional)

## Deployment Options

### 1. Docker Compose (Development)

```bash
# Start all services
make up

# Verify
make verify
```

### 2. Kubernetes (Production)

#### Build and Push Images

```bash
# Build all images
docker-compose build

# Tag images
docker tag optiinfra-orchestrator:latest your-registry/optiinfra-orchestrator:v1.0.0
docker tag optiinfra-cost-agent:latest your-registry/optiinfra-cost-agent:v1.0.0
# ... repeat for all services

# Push to registry
docker push your-registry/optiinfra-orchestrator:v1.0.0
docker push your-registry/optiinfra-cost-agent:v1.0.0
# ... repeat for all services
```

#### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace optiinfra

# Apply base manifests
kubectl apply -k k8s/base

# Or apply environment-specific overlays
kubectl apply -k k8s/overlays/production
```

#### Verify Deployment

```bash
# Check pods
kubectl get pods -n optiinfra

# Check services
kubectl get svc -n optiinfra

# Check logs
kubectl logs -f deployment/optiinfra-orchestrator -n optiinfra
```

## Configuration

### Secrets

Create Kubernetes secrets for sensitive data:

```bash
# Database credentials
kubectl create secret generic postgres-credentials \
  --from-literal=username=optiinfra \
  --from-literal=password=your-password \
  -n optiinfra

# API keys
kubectl create secret generic api-keys \
  --from-literal=openai-api-key=sk-your-key \
  --from-literal=anthropic-api-key=sk-ant-your-key \
  -n optiinfra

# Cloud provider credentials
kubectl create secret generic aws-credentials \
  --from-file=credentials=~/.aws/credentials \
  -n optiinfra
```

### ConfigMaps

```bash
kubectl create configmap optiinfra-config \
  --from-file=config.yaml \
  -n optiinfra
```

## Scaling

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: orchestrator-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: optiinfra-orchestrator
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Manual Scaling

```bash
kubectl scale deployment optiinfra-orchestrator --replicas=5 -n optiinfra
```

## Monitoring

### Prometheus

```bash
# Install Prometheus (if not already installed)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Configure ServiceMonitor for OptiInfra
kubectl apply -f k8s/monitoring/service-monitor.yaml
```

### Grafana

```bash
# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Import OptiInfra dashboards
# Dashboards are in k8s/monitoring/dashboards/
```

## Backup and Recovery

### Database Backups

```bash
# PostgreSQL backup
kubectl exec -n optiinfra postgres-0 -- pg_dump -U optiinfra optiinfra > backup.sql

# Restore
kubectl exec -i -n optiinfra postgres-0 -- psql -U optiinfra optiinfra < backup.sql
```

### ClickHouse Backups

```bash
# Backup
kubectl exec -n optiinfra clickhouse-0 -- clickhouse-backup create

# Restore
kubectl exec -n optiinfra clickhouse-0 -- clickhouse-backup restore backup-name
```

## CI/CD

### GitHub Actions

See `.github/workflows/deploy.yml` for automated deployment pipeline.

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push images
        run: |
          docker-compose build
          docker-compose push
      - name: Deploy to Kubernetes
        run: |
          kubectl apply -k k8s/overlays/production
```

## Health Checks

All services expose health check endpoints:

- Orchestrator: `http://orchestrator:8080/health`
- Cost Agent: `http://cost-agent:8001/health`
- Performance Agent: `http://performance-agent:8002/health`
- Resource Agent: `http://resource-agent:8003/health`
- Application Agent: `http://application-agent:8004/health`

## Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/optiinfra-orchestrator -n optiinfra

# Check rollout status
kubectl rollout status deployment/optiinfra-orchestrator -n optiinfra
```

## Security Considerations

- Use network policies to restrict traffic
- Enable RBAC for all services
- Use secrets for sensitive data
- Enable TLS for all external endpoints
- Regular security scanning of images
- Keep dependencies up to date

## Cost Optimization

- Use spot instances for non-critical workloads
- Enable cluster autoscaling
- Set resource requests and limits
- Use horizontal pod autoscaling
- Monitor and optimize resource usage
