# PHASE2: Performance Agent - Comprehensive Documentation (Part 4/5)

**Version**: 1.0.0  
**Last Updated**: October 26, 2025  
**Document Part**: D.4 - Configuration, Testing, Deployment

---

## 10. Configuration

### Environment Variables
```bash
GROQ_API_KEY=your_key
AGENT_NAME=performance-agent
PORT=8002
GROQ_MODEL=gpt-oss-20b
LLM_TIMEOUT=30
LLM_MAX_RETRIES=3
ORCHESTRATOR_URL=http://localhost:8080
```

---

## 11. Testing & Validation

### Test Coverage
- Unit Tests: 80%+
- Integration Tests: 70%+
- Performance Tests: Included

### Running Tests
```bash
pytest tests/ -v --cov=src
```

---

## 12. Deployment

### Quick Start
```bash
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn src.main:app --reload --port 8002
curl http://localhost:8002/health
```

### Docker
```bash
docker build -t performance-agent:1.0.0 .
docker run -d -p 8002:8002 --env-file .env performance-agent:1.0.0
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: performance-agent
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: performance-agent
        image: performance-agent:1.0.0
        ports:
        - containerPort: 8002
```

---

**End of Part 4/5**
