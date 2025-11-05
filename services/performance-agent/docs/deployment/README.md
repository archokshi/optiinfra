# Performance Agent Deployment Guide

## Prerequisites

- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for container deployment)
- **Kubernetes**: 1.24+ (for K8s deployment)
- **Network**: Access to LLM instance metrics endpoints

## Local Development

### 1. Install Dependencies

```bash
cd services/performance-agent

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Environment Variables**:
```bash
# Agent Configuration
AGENT_ID=performance-agent
AGENT_VERSION=1.0.0

# Orchestrator
ORCHESTRATOR_URL=http://localhost:8080

# Polling Configuration
POLLING_INTERVAL=30
METRICS_TIMEOUT=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Server
PORT=8002
WORKERS=1
```

### 3. Run the Agent

```bash
# Development mode with hot reload
uvicorn src.main:app --reload --port 8002

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8002 --workers 4
```

### 4. Verify Installation

```bash
# Check health
curl http://localhost:8002/api/v1/health

# Check detailed health
curl http://localhost:8002/api/v1/health/detailed

# View API docs
open http://localhost:8002/docs
```

---

## Docker Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t performance-agent:latest .

# Build with specific version
docker build -t performance-agent:1.0.0 .
```

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8002/api/v1/health || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8002"]
```

### 2. Run Container

```bash
# Run with default settings
docker run -d \
  --name performance-agent \
  -p 8002:8002 \
  performance-agent:latest

# Run with custom environment
docker run -d \
  --name performance-agent \
  -p 8002:8002 \
  -e AGENT_ID=performance-agent-1 \
  -e ORCHESTRATOR_URL=http://orchestrator:8080 \
  -e LOG_LEVEL=DEBUG \
  performance-agent:latest

# Run with environment file
docker run -d \
  --name performance-agent \
  -p 8002:8002 \
  --env-file .env \
  performance-agent:latest
```

### 3. Verify Container

```bash
# Check container status
docker ps | grep performance-agent

# View logs
docker logs performance-agent

# Follow logs
docker logs -f performance-agent

# Check health
docker exec performance-agent curl http://localhost:8002/api/v1/health
```

### 4. Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  performance-agent:
    build: .
    image: performance-agent:latest
    container_name: performance-agent
    ports:
      - "8002:8002"
    environment:
      - AGENT_ID=performance-agent
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
    restart: unless-stopped
    networks:
      - optiinfra

networks:
  optiinfra:
    external: true
```

**Run with Docker Compose**:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f performance-agent

# Stop services
docker-compose down
```

---

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace optiinfra
```

### 2. Create ConfigMap

**k8s/configmap.yaml**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: performance-agent-config
  namespace: optiinfra
data:
  AGENT_ID: "performance-agent"
  ORCHESTRATOR_URL: "http://orchestrator:8080"
  POLLING_INTERVAL: "30"
  LOG_LEVEL: "INFO"
  PORT: "8002"
```

```bash
kubectl apply -f k8s/configmap.yaml
```

### 3. Create Deployment

**k8s/deployment.yaml**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: performance-agent
  namespace: optiinfra
  labels:
    app: performance-agent
    version: v1
spec:
  replicas: 2
  selector:
    matchLabels:
      app: performance-agent
  template:
    metadata:
      labels:
        app: performance-agent
        version: v1
    spec:
      containers:
      - name: performance-agent
        image: performance-agent:1.0.0
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8002
          name: http
          protocol: TCP
        envFrom:
        - configMapRef:
            name: performance-agent-config
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /api/v1/health
            port: 8002
          initialDelaySeconds: 10
          periodSeconds: 30
          timeoutSeconds: 5
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /api/v1/health/detailed
            port: 8002
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
```

```bash
kubectl apply -f k8s/deployment.yaml
```

### 4. Create Service

**k8s/service.yaml**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: performance-agent
  namespace: optiinfra
  labels:
    app: performance-agent
spec:
  type: ClusterIP
  selector:
    app: performance-agent
  ports:
  - port: 8002
    targetPort: 8002
    protocol: TCP
    name: http
```

```bash
kubectl apply -f k8s/service.yaml
```

### 5. Create Ingress (Optional)

**k8s/ingress.yaml**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: performance-agent
  namespace: optiinfra
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: performance-agent.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: performance-agent
            port:
              number: 8002
```

```bash
kubectl apply -f k8s/ingress.yaml
```

### 6. Verify Deployment

```bash
# Check pods
kubectl get pods -n optiinfra -l app=performance-agent

# Check service
kubectl get svc -n optiinfra performance-agent

# View logs
kubectl logs -n optiinfra -l app=performance-agent -f

# Port forward for testing
kubectl port-forward -n optiinfra svc/performance-agent 8002:8002

# Test health
curl http://localhost:8002/api/v1/health
```

### 7. Horizontal Pod Autoscaler (Optional)

**k8s/hpa.yaml**:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: performance-agent
  namespace: optiinfra
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: performance-agent
  minReplicas: 2
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
```

```bash
kubectl apply -f k8s/hpa.yaml
```

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AGENT_ID` | Unique agent identifier | `performance-agent` | No |
| `AGENT_VERSION` | Agent version | `1.0.0` | No |
| `ORCHESTRATOR_URL` | Orchestrator endpoint | `http://localhost:8080` | Yes |
| `POLLING_INTERVAL` | Metrics polling interval (seconds) | `30` | No |
| `METRICS_TIMEOUT` | Metrics collection timeout (seconds) | `10` | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `LOG_FORMAT` | Log format (json, text) | `json` | No |
| `PORT` | Server port | `8002` | No |
| `WORKERS` | Number of worker processes | `1` | No |

### Threshold Configuration

Create `config/thresholds.yaml`:
```yaml
thresholds:
  memory_usage: 0.8        # 80%
  ttft: 0.1                # 100ms
  throughput: 100.0        # tokens/sec
  queue_depth: 10          # requests
  cache_hit_rate: 0.7      # 70%
```

---

## Monitoring

### Health Checks

**Liveness Probe**:
```bash
curl http://localhost:8002/api/v1/health
```

**Readiness Probe**:
```bash
curl http://localhost:8002/api/v1/health/detailed
```

### Prometheus Metrics

The agent exposes metrics at `/metrics`:

```bash
curl http://localhost:8002/metrics
```

**Key Metrics**:
- `performance_agent_requests_total` - Total requests
- `performance_agent_request_duration_seconds` - Request duration
- `performance_agent_errors_total` - Total errors
- `performance_agent_workflows_active` - Active workflows

### Grafana Dashboard

Import the provided Grafana dashboard:
```bash
# Dashboard JSON in docs/monitoring/grafana-dashboard.json
```

---

## Troubleshooting

### Agent Not Starting

**Check logs**:
```bash
# Docker
docker logs performance-agent

# Kubernetes
kubectl logs -n optiinfra -l app=performance-agent
```

**Common issues**:
- Missing environment variables
- Port already in use
- Invalid configuration

### Cannot Connect to Instances

**Verify network connectivity**:
```bash
# From agent container
docker exec performance-agent curl http://vllm-instance:8000/metrics

# From K8s pod
kubectl exec -n optiinfra performance-agent-xxx -- curl http://vllm-instance:8000/metrics
```

**Check DNS resolution**:
```bash
nslookup vllm-instance
```

### High Memory Usage

**Check resource usage**:
```bash
# Docker
docker stats performance-agent

# Kubernetes
kubectl top pod -n optiinfra -l app=performance-agent
```

**Solutions**:
- Reduce worker count
- Increase memory limits
- Enable garbage collection

### Slow Response Times

**Check performance**:
```bash
# Run load tests
pytest tests/performance/ -v

# Check metrics
curl http://localhost:8002/metrics | grep duration
```

**Solutions**:
- Increase workers
- Optimize database queries
- Add caching

---

## Backup and Recovery

### Backup Configuration

```bash
# Backup environment file
cp .env .env.backup

# Backup Kubernetes configs
kubectl get configmap -n optiinfra performance-agent-config -o yaml > backup/configmap.yaml
```

### Recovery

```bash
# Restore from backup
cp .env.backup .env

# Redeploy
kubectl apply -f k8s/
```

---

## Upgrade Guide

### Rolling Update (Kubernetes)

```bash
# Update image
kubectl set image deployment/performance-agent \
  performance-agent=performance-agent:1.1.0 \
  -n optiinfra

# Check rollout status
kubectl rollout status deployment/performance-agent -n optiinfra

# Rollback if needed
kubectl rollout undo deployment/performance-agent -n optiinfra
```

### Zero-Downtime Update (Docker)

```bash
# Start new version
docker run -d --name performance-agent-new -p 8003:8002 performance-agent:1.1.0

# Verify new version
curl http://localhost:8003/api/v1/health

# Update load balancer to point to new version
# Stop old version
docker stop performance-agent
docker rm performance-agent

# Rename new version
docker rename performance-agent-new performance-agent
```

---

## Security Hardening

### Production Checklist

- [ ] Enable TLS/HTTPS
- [ ] Implement authentication
- [ ] Set up rate limiting
- [ ] Use secrets management
- [ ] Enable audit logging
- [ ] Restrict network access
- [ ] Run as non-root user
- [ ] Scan images for vulnerabilities

---

**Last Updated**: 2024-01-01  
**Version**: 1.0.0
