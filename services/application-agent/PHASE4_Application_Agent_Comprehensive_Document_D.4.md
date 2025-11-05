# PHASE4: Application Agent - Comprehensive Documentation (Part 4/5)

**Version**: 1.0.0  
**Last Updated**: October 26, 2025  
**Document Part**: D.4 - Configuration, Testing, Deployment

---

## 10. Configuration

### Environment Variables

#### Required Variables

```bash
# Groq API Configuration (REQUIRED)
GROQ_API_KEY=your_groq_api_key_here
```

#### Optional Variables

```bash
# Agent Configuration
AGENT_NAME=application-agent
AGENT_ID=app-agent-001
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development  # development, staging, production

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json  # json, text

# LLM Configuration
GROQ_MODEL=gpt-oss-20b
LLM_TIMEOUT=30  # seconds
LLM_MAX_RETRIES=3
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000

# Orchestrator Configuration
ORCHESTRATOR_URL=http://localhost:8080
REGISTRATION_ENABLED=true
HEARTBEAT_INTERVAL=30  # seconds
HEARTBEAT_TIMEOUT=10  # seconds

# Quality Thresholds
QUALITY_THRESHOLD=80.0
RELEVANCE_THRESHOLD=85.0
COHERENCE_THRESHOLD=80.0
HALLUCINATION_THRESHOLD=10.0

# Regression Detection
REGRESSION_THRESHOLD=5.0  # percentage
BASELINE_SAMPLE_SIZE=100

# Validation
AUTO_APPROVE_THRESHOLD=90.0
AUTO_REJECT_THRESHOLD=70.0

# Performance
MAX_WORKERS=4
REQUEST_TIMEOUT=60  # seconds
MAX_CONNECTIONS=100

# Storage (Future)
DATABASE_URL=postgresql://user:pass@localhost:5432/appagent
REDIS_URL=redis://localhost:6379/0

# Monitoring
METRICS_ENABLED=true
METRICS_PORT=9090
TRACING_ENABLED=false
```

### Configuration File

**Location**: `src/core/config.py`

```python
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings."""
    
    # Agent Configuration
    agent_name: str = "application-agent"
    agent_id: str = "app-agent-001"
    version: str = "1.0.0"
    port: int = 8000
    host: str = "0.0.0.0"
    environment: str = "development"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Groq/LLM Configuration
    groq_api_key: str
    groq_model: str = "gpt-oss-20b"
    llm_timeout: int = 30
    llm_max_retries: int = 3
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1000
    
    # Orchestrator Configuration
    orchestrator_url: str = "http://localhost:8080"
    registration_enabled: bool = True
    heartbeat_interval: int = 30
    heartbeat_timeout: int = 10
    
    # Quality Thresholds
    quality_threshold: float = 80.0
    relevance_threshold: float = 85.0
    coherence_threshold: float = 80.0
    hallucination_threshold: float = 10.0
    
    # Regression Detection
    regression_threshold: float = 5.0
    baseline_sample_size: int = 100
    
    # Validation
    auto_approve_threshold: float = 90.0
    auto_reject_threshold: float = 70.0
    
    # Performance
    max_workers: int = 4
    request_timeout: int = 60
    max_connections: int = 100
    
    # Storage (Future)
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Monitoring
    metrics_enabled: bool = True
    metrics_port: int = 9090
    tracing_enabled: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Configuration Examples

#### Development Configuration

```bash
# .env.development
ENVIRONMENT=development
LOG_LEVEL=DEBUG
GROQ_API_KEY=your_dev_key
ORCHESTRATOR_URL=http://localhost:8080
REGISTRATION_ENABLED=false
```

#### Staging Configuration

```bash
# .env.staging
ENVIRONMENT=staging
LOG_LEVEL=INFO
GROQ_API_KEY=your_staging_key
ORCHESTRATOR_URL=http://staging-orchestrator:8080
REGISTRATION_ENABLED=true
METRICS_ENABLED=true
```

#### Production Configuration

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING
GROQ_API_KEY=your_prod_key
ORCHESTRATOR_URL=http://orchestrator.prod.internal:8080
REGISTRATION_ENABLED=true
HEARTBEAT_INTERVAL=30
METRICS_ENABLED=true
TRACING_ENABLED=true
DATABASE_URL=postgresql://user:pass@db.prod.internal:5432/appagent
REDIS_URL=redis://cache.prod.internal:6379/0
```

### Configuration Best Practices

1. **Never commit secrets**: Use `.env` files (gitignored)
2. **Use environment-specific configs**: Separate dev/staging/prod
3. **Validate on startup**: Pydantic validates all settings
4. **Document all variables**: Keep `.env.example` updated
5. **Use secure defaults**: Fail-safe configuration values
6. **Monitor configuration changes**: Track config modifications

---

## 11. Testing & Validation

### Test Coverage

| Test Type | Coverage | Files | Purpose |
|-----------|----------|-------|---------|
| **Unit Tests** | 85%+ | `tests/unit/*` | Component testing |
| **Integration Tests** | 75%+ | `tests/integration/*` | API testing |
| **Performance Tests** | N/A | `tests/performance/*` | Load testing |

### Unit Tests

**Location**: `tests/unit/`

**Structure**:
```
tests/unit/
├── test_quality_collector.py
├── test_quality_analyzer.py
├── test_regression_detector.py
├── test_validation_engine.py
├── test_workflow.py
├── test_llm_client.py
├── test_config_tracker.py
└── test_api_endpoints.py
```

**Running Unit Tests**:
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_quality_collector.py -v

# Run with coverage
pytest tests/unit/ -v --cov=src --cov-report=html

# Run with markers
pytest tests/unit/ -v -m "not slow"
```

**Example Unit Test**:
```python
import pytest
from src.collectors.quality_collector import QualityCollector

def test_quality_collector_basic():
    """Test basic quality collection."""
    collector = QualityCollector()
    
    result = collector.collect(
        prompt="What is AI?",
        response="AI is artificial intelligence..."
    )
    
    assert result['relevance'] >= 0
    assert result['relevance'] <= 100
    assert result['coherence'] >= 0
    assert result['coherence'] <= 100
    assert 'quality_score' in result

@pytest.mark.asyncio
async def test_quality_collector_async():
    """Test async quality collection."""
    collector = QualityCollector()
    
    result = await collector.collect_async(
        prompt="What is AI?",
        response="AI is artificial intelligence..."
    )
    
    assert result is not None
```

### Integration Tests

**Location**: `tests/integration/`

**Structure**:
```
tests/integration/
├── test_api_integration.py
├── test_workflow_integration.py
├── test_llm_integration.py
└── test_orchestrator_integration.py
```

**Running Integration Tests**:
```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with real services
pytest tests/integration/ -v --use-real-services

# Run specific integration test
pytest tests/integration/test_api_integration.py -v
```

**Example Integration Test**:
```python
import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_quality_analysis_integration():
    """Test complete quality analysis flow."""
    # Step 1: Analyze quality
    response = client.post(
        "/quality/analyze",
        json={
            "prompt": "What is AI?",
            "response": "AI is artificial intelligence...",
            "model_id": "gpt-4"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'quality_score' in data
    
    # Step 2: Get insights
    response = client.get("/quality/insights")
    assert response.status_code == 200
    
    # Step 3: Get trend
    response = client.get("/quality/trend?model_id=gpt-4&period=7d")
    assert response.status_code == 200
```

### Performance Tests

**Location**: `tests/performance/`

**Structure**:
```
tests/performance/
├── locustfile.py
├── test_scenarios.py
└── __init__.py
```

**Running Performance Tests**:
```bash
# Run Locust with web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Run headless
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless

# Run with custom script
python scripts/run_performance_tests.py
```

**Locust Test Scenarios**:
```python
from locust import HttpUser, task, between

class ApplicationAgentUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def analyze_quality(self):
        """Test quality analysis endpoint."""
        self.client.post(
            "/quality/analyze",
            json={
                "prompt": "What is AI?",
                "response": "AI is artificial intelligence...",
                "model_id": "gpt-4"
            }
        )
    
    @task(2)
    def detect_regression(self):
        """Test regression detection."""
        self.client.post(
            "/regression/detect",
            json={
                "model_name": "gpt-4",
                "config_hash": "v1.0.0",
                "current_quality": 85.0
            }
        )
    
    @task(1)
    def get_health(self):
        """Test health endpoint."""
        self.client.get("/health")
```

### Test Fixtures

**Location**: `tests/fixtures/`

**Example Fixtures**:
```python
import pytest
from src.main import app
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def sample_quality_data():
    """Sample quality analysis data."""
    return {
        "prompt": "What is AI?",
        "response": "AI is artificial intelligence...",
        "model_id": "gpt-4"
    }

@pytest.fixture
def sample_baseline():
    """Sample baseline data."""
    return {
        "model_name": "gpt-4",
        "config_hash": "v1.0.0",
        "average_quality": 85.0,
        "sample_size": 100
    }
```

### Validation Checklist

#### Pre-Deployment Validation

- [ ] All unit tests pass (85%+ coverage)
- [ ] All integration tests pass
- [ ] Performance tests meet targets
- [ ] API documentation up to date
- [ ] Configuration validated
- [ ] Security scan passed
- [ ] Code review completed
- [ ] Linting passed (flake8, mypy)
- [ ] Dependencies up to date

#### Post-Deployment Validation

- [ ] Health checks passing
- [ ] Orchestrator registration successful
- [ ] All endpoints responding
- [ ] Metrics being collected
- [ ] Logs being generated
- [ ] No errors in logs
- [ ] Performance within targets
- [ ] Integration with other agents working

---

## 12. Deployment

### Prerequisites

**Software Requirements**:
- Python 3.11+
- pip or poetry
- Docker (optional)
- Kubernetes (optional)
- Git

**Infrastructure Requirements**:
- 2+ CPU cores (4 recommended)
- 4+ GB RAM (8 GB recommended)
- 10+ GB storage
- Network connectivity
- Port 8000 available

**External Services**:
- Groq API access (API key required)
- Orchestrator running (PHASE0)

### Local Development Deployment

#### Step 1: Clone Repository

```bash
git clone https://github.com/your-org/optiinfra.git
cd optiinfra/services/application-agent
```

#### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

#### Step 3: Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env

# Add required variables
GROQ_API_KEY=your_groq_api_key_here
```

#### Step 5: Run Application

```bash
# Run with uvicorn
python -m uvicorn src.main:app --reload --port 8000

# Or run directly
python src/main.py
```

#### Step 6: Verify Deployment

```bash
# Check health
curl http://localhost:8000/health

# Check detailed health
curl http://localhost:8000/health/detailed

# View API docs
open http://localhost:8000/docs
```

### Docker Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY .env.example .env

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Run

```bash
# Build image
docker build -t application-agent:1.0.0 .

# Run container
docker run -d \
  --name application-agent \
  -p 8000:8000 \
  --env-file .env \
  application-agent:1.0.0

# Check logs
docker logs -f application-agent

# Check health
curl http://localhost:8000/health
```

#### Docker Compose

```yaml
version: '3.8'

services:
  application-agent:
    build: .
    container_name: application-agent
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - ORCHESTRATOR_URL=http://orchestrator:8080
      - ENVIRONMENT=production
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
    networks:
      - optiinfra

networks:
  optiinfra:
    external: true
```

**Run with Docker Compose**:
```bash
docker-compose up -d
```

### Kubernetes Deployment

#### Deployment YAML

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: application-agent
  namespace: optiinfra
  labels:
    app: application-agent
    version: v1.0.0
spec:
  replicas: 3
  selector:
    matchLabels:
      app: application-agent
  template:
    metadata:
      labels:
        app: application-agent
        version: v1.0.0
    spec:
      containers:
      - name: application-agent
        image: application-agent:1.0.0
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: application-agent-secrets
              key: groq-api-key
        - name: ORCHESTRATOR_URL
          value: "http://orchestrator:8080"
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: application-agent
  namespace: optiinfra
spec:
  selector:
    app: application-agent
  ports:
  - protocol: TCP
    port: 8000
    targetPort: 8000
  type: ClusterIP
---
apiVersion: v1
kind: Secret
metadata:
  name: application-agent-secrets
  namespace: optiinfra
type: Opaque
stringData:
  groq-api-key: "your_groq_api_key_here"
```

#### Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace optiinfra

# Apply configuration
kubectl apply -f k8s/application-agent.yaml

# Check deployment
kubectl get pods -n optiinfra -l app=application-agent

# Check logs
kubectl logs -n optiinfra -l app=application-agent -f

# Check service
kubectl get svc -n optiinfra application-agent
```

### Production Deployment Checklist

#### Pre-Deployment

- [ ] Environment variables configured
- [ ] Secrets stored securely (Vault, K8s Secrets)
- [ ] Database migrations completed (if applicable)
- [ ] Load balancer configured
- [ ] SSL/TLS certificates installed
- [ ] Monitoring configured
- [ ] Alerting configured
- [ ] Backup strategy in place
- [ ] Rollback plan documented

#### Deployment

- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Verify health checks
- [ ] Check metrics
- [ ] Monitor logs
- [ ] Gradual rollout (canary/blue-green)
- [ ] Monitor error rates
- [ ] Verify integration with other services

#### Post-Deployment

- [ ] All health checks passing
- [ ] Metrics being collected
- [ ] Logs being aggregated
- [ ] Alerts configured
- [ ] Performance within targets
- [ ] No errors in production
- [ ] Documentation updated
- [ ] Team notified

### Production Considerations

#### High Availability

```yaml
# Multiple replicas
replicas: 3

# Pod anti-affinity
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchExpressions:
          - key: app
            operator: In
            values:
            - application-agent
        topologyKey: kubernetes.io/hostname
```

#### Auto-Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: application-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: application-agent
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
```

#### Security

```bash
# Use non-root user
USER 1000:1000

# Read-only filesystem
readOnlyRootFilesystem: true

# Drop capabilities
securityContext:
  capabilities:
    drop:
    - ALL
  runAsNonRoot: true
  runAsUser: 1000
```

#### Monitoring

```yaml
# Prometheus annotations
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "9090"
  prometheus.io/path: "/metrics"
```

#### Logging

```yaml
# Structured logging
LOG_FORMAT=json
LOG_LEVEL=INFO

# Log aggregation (Fluentd, Logstash)
```

### Rollback Procedure

```bash
# Kubernetes rollback
kubectl rollout undo deployment/application-agent -n optiinfra

# Docker rollback
docker stop application-agent
docker rm application-agent
docker run -d --name application-agent application-agent:1.0.0-previous

# Verify rollback
curl http://localhost:8000/health
```

---

**End of Part 4/5**

**Next**: Part 5 covers "Integration", "Monitoring", "Security", "Limitations", "References", "Version History", "Quick Reference", and Appendices

**To combine**: Concatenate D.1, D.2, D.3, D.4, D.5 in order.
