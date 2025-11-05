# PHASE3: Resource Agent - Comprehensive Documentation (Part 4/5)

**Version**: 1.0.0  
**Last Updated**: October 26, 2025  
**Document Part**: D.4 - Configuration, Testing, Deployment

---

## 10. Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here

# Agent Configuration
AGENT_NAME=resource-agent
AGENT_ID=resource-agent-001
PORT=8003
ENVIRONMENT=development

# LLM Configuration
GROQ_MODEL=gpt-oss-20b
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3

# Orchestrator
ORCHESTRATOR_URL=http://localhost:8080
REGISTRATION_ENABLED=true
HEARTBEAT_INTERVAL=30

# Monitoring
GPU_MONITORING_ENABLED=true
METRICS_COLLECTION_INTERVAL=5
```

### Configuration File

Location: `src/config.py`

```python
class Settings(BaseSettings):
    agent_name: str = "resource-agent"
    agent_id: str = "resource-agent-001"
    port: int = 8003
    groq_api_key: str
    groq_model: str = "gpt-oss-20b"
    orchestrator_url: str = "http://localhost:8080"
    gpu_monitoring_enabled: bool = True
    metrics_collection_interval: int = 5
```

---

## 11. Testing & Validation

### Test Coverage

| Test Type | Coverage | Files |
|-----------|----------|-------|
| Unit Tests | 80%+ | `tests/unit/*` |
| Integration Tests | 70%+ | `tests/integration/*` |

### Running Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest tests/ -v --cov=src
```

---

## 12. Deployment

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add GROQ_API_KEY

# Run the agent
python -m uvicorn src.main:app --reload --port 8003

# Test
curl http://localhost:8003/health
```

### Docker Deployment

```bash
# Build
docker build -t resource-agent:1.0.0 .

# Run
docker run -d \
  --name resource-agent \
  -p 8003:8003 \
  --env-file .env \
  resource-agent:1.0.0
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-agent
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: resource-agent
        image: resource-agent:1.0.0
        ports:
        - containerPort: 8003
        env:
        - name: GROQ_API_KEY
          valueFrom:
            secretKeyRef:
              name: resource-agent-secrets
              key: groq-api-key
```

---

**End of Part 4/5**

**Next**: Part 5 covers Integration, Monitoring, Security, References
