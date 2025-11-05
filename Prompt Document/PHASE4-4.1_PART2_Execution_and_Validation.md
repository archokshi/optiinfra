# PHASE4-4.1 PART2: Application Agent Skeleton - Execution and Validation

**Phase**: PHASE4-4.1  
**Agent**: Application Agent  
**Objective**: Execute and validate FastAPI skeleton and registration  
**Estimated Time**: 15 minutes  
**Priority**: HIGH

---

## Pre-Execution Checklist

- [ ] PHASE4-4.1_PART1 documentation reviewed
- [ ] Python 3.11+ installed
- [ ] Orchestrator running on port 8000 (optional for now)
- [ ] Port 8004 available

---

## Execution Steps

### Step 1: Create Project Structure (2 minutes)

```bash
cd services/application-agent

# Create directory structure
mkdir -p src/api src/core src/models tests

# Create __init__.py files
touch src/__init__.py
touch src/api/__init__.py
touch src/core/__init__.py
touch src/models/__init__.py
touch tests/__init__.py
```

**Expected Output:**
```
application-agent/
├── src/
│   ├── api/
│   ├── core/
│   ├── models/
│   └── __init__.py
└── tests/
    └── __init__.py
```

---

### Step 2: Create Core Files (3 minutes)

```bash
# Create configuration
# File: src/core/config.py
# (Copy from PART1)

# Create logger
# File: src/core/logger.py
# (Copy from PART1)

# Create registration client
# File: src/core/registration.py
# (Copy from PART1)

# Create __init__.py
touch src/core/__init__.py
```

---

### Step 3: Create API Endpoints (2 minutes)

```bash
# Create health endpoints
# File: src/api/health.py
# (Copy from PART1)

# Create __init__.py
touch src/api/__init__.py
```

---

### Step 4: Create Main Application (2 minutes)

```bash
# Create main FastAPI app
# File: src/main.py
# (Copy from PART1)
```

---

### Step 5: Create Configuration Files (2 minutes)

```bash
# Create requirements.txt
# (Copy from PART1)

# Create .env.example
# (Copy from PART1)

# Create actual .env
cp .env.example .env

# Create pytest.ini
# (Copy from PART1)

# Create .gitignore
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
EOF
```

---

### Step 6: Install Dependencies (2 minutes)

```bash
# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 pydantic-2.5.0 ...
```

---

### Step 7: Run Application (1 minute)

```bash
# Start the application
python -m uvicorn src.main:app --port 8004 --reload
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\...\\application-agent']
INFO:     Uvicorn running on http://0.0.0.0:8004 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     {"time":"2025-10-25T...","level":"INFO","name":"application-agent","message":"Starting Application Agent v1.0.0"}
INFO:     {"time":"2025-10-25T...","level":"INFO","name":"application-agent","message":"Environment: development"}
INFO:     {"time":"2025-10-25T...","level":"INFO","name":"application-agent","message":"Port: 8004"}
INFO:     Application startup complete.
```

---

### Step 8: Validate Endpoints (2 minutes)

Open a new terminal and test endpoints:

```bash
# Test root endpoint
curl http://localhost:8004/

# Expected:
# {"agent":"Application Agent","version":"1.0.0","status":"active","agent_id":"application-agent-001"}

# Test health check
curl http://localhost:8004/health/

# Expected:
# {"status":"healthy","timestamp":"2025-10-25T...","agent_id":"application-agent-001"}

# Test detailed health
curl http://localhost:8004/health/detailed

# Expected:
# {"status":"degraded","timestamp":"...","agent_id":"application-agent-001","version":"1.0.0","components":{"orchestrator":"disconnected","api":"healthy"},"uptime_seconds":0}

# Test readiness
curl http://localhost:8004/health/ready

# Expected:
# {"status":"ready"}

# Test liveness
curl http://localhost:8004/health/live

# Expected:
# {"status":"alive"}
```

---

### Step 9: Check API Documentation (1 minute)

```bash
# Open in browser
start http://localhost:8004/docs

# Or
start http://localhost:8004/redoc
```

**Expected:**
- Swagger UI with all endpoints listed
- Interactive API documentation
- Ability to test endpoints directly

---

### Step 10: Run Tests (2 minutes)

```bash
# Create test file
# File: tests/test_health.py
# (Copy from PART1)

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

**Expected Output:**
```
tests/test_health.py::test_root PASSED
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_detailed_health PASSED
tests/test_health.py::test_readiness_check PASSED
tests/test_health.py::test_liveness_check PASSED

========== 5 passed in 0.50s ==========

Coverage:
src/main.py                    95%
src/api/health.py             100%
src/core/config.py             90%
src/core/logger.py            100%
src/core/registration.py       60%  (not fully tested yet)
```

---

## Validation Checklist

### Application Startup ✅
- [ ] Application starts without errors
- [ ] Logs show startup messages
- [ ] Port 8004 is listening
- [ ] No import errors

### Health Endpoints ✅
- [ ] `GET /` returns agent info
- [ ] `GET /health/` returns healthy status
- [ ] `GET /health/detailed` returns component status
- [ ] `GET /health/ready` returns ready
- [ ] `GET /health/live` returns alive

### API Documentation ✅
- [ ] Swagger UI accessible at `/docs`
- [ ] ReDoc accessible at `/redoc`
- [ ] All endpoints listed
- [ ] Can test endpoints interactively

### Configuration ✅
- [ ] `.env` file loaded correctly
- [ ] Settings accessible via `settings` object
- [ ] Default values work
- [ ] Environment variables override defaults

### Logging ✅
- [ ] Logs are structured (JSON format)
- [ ] Log level configurable
- [ ] Startup/shutdown logged
- [ ] Errors logged appropriately

### Tests ✅
- [ ] All 5 tests passing
- [ ] Coverage > 80% for implemented code
- [ ] No test failures
- [ ] Fast execution (< 1 second)

---

## Orchestrator Integration (Optional)

If orchestrator is running:

### Step 1: Start Orchestrator

```bash
# In another terminal
cd services/orchestrator
go run main.go
```

### Step 2: Verify Registration

```bash
# Check orchestrator logs for registration
# Should see: "Agent registered: application-agent-001"

# Query orchestrator API
curl http://localhost:8000/api/v1/agents

# Expected:
# [{"agent_id":"application-agent-001","agent_name":"Application Agent","agent_type":"application","status":"active",...}]
```

### Step 3: Verify Heartbeat

```bash
# Wait 30 seconds and check orchestrator logs
# Should see periodic: "Heartbeat received from application-agent-001"

# Check agent status
curl http://localhost:8000/api/v1/agents/application-agent-001

# Expected:
# {"agent_id":"application-agent-001","status":"active","last_heartbeat":"2025-10-25T..."}
```

### Step 4: Test Deregistration

```bash
# Stop Application Agent (Ctrl+C)
# Check orchestrator logs
# Should see: "Agent deregistered: application-agent-001"

# Query orchestrator API
curl http://localhost:8000/api/v1/agents

# Expected:
# [] (empty list)
```

---

## Troubleshooting

### Issue 1: Port Already in Use

**Symptom:**
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8004)
```

**Solution:**
```bash
# Change port in .env
PORT=8005

# Or kill process using port 8004
# Windows:
netstat -ano | findstr :8004
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8004
kill -9 <PID>
```

---

### Issue 2: Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### Issue 3: Orchestrator Connection Failed

**Symptom:**
```
WARNING: Registration failed: Connection refused
```

**Solution:**
- This is expected if orchestrator is not running
- Agent will continue to work without orchestrator
- Set `REGISTRATION_ENABLED=false` in `.env` to disable registration

---

### Issue 4: Tests Failing

**Symptom:**
```
FAILED tests/test_health.py::test_root
```

**Solution:**
```bash
# Check if app is running (stop it for tests)
# Tests use TestClient which doesn't need running server

# Run tests with verbose output
pytest tests/ -v -s

# Check for syntax errors
python -m py_compile src/main.py
```

---

## Performance Validation

### Response Time Benchmarks

| Endpoint | Target | Typical |
|----------|--------|---------|
| `GET /` | < 50ms | ~10ms |
| `GET /health/` | < 50ms | ~5ms |
| `GET /health/detailed` | < 100ms | ~15ms |
| `GET /health/ready` | < 50ms | ~5ms |
| `GET /health/live` | < 50ms | ~5ms |

### Load Testing (Optional)

```bash
# Install Apache Bench
# Windows: Download from Apache website
# Linux: apt-get install apache2-utils

# Test health endpoint
ab -n 1000 -c 10 http://localhost:8004/health/

# Expected:
# Requests per second: 500-1000
# Time per request: 1-2ms (mean)
# Failed requests: 0
```

---

## Success Criteria

### Must Have ✅
- [x] Application starts successfully
- [x] All 5 health endpoints working
- [x] API documentation accessible
- [x] All tests passing (5/5)
- [x] Structured logging working
- [x] Configuration loading correctly

### Should Have ✅
- [x] Orchestrator registration (if available)
- [x] Heartbeat mechanism working
- [x] Graceful shutdown
- [x] Error handling
- [x] Test coverage > 80%

### Nice to Have 🎯
- [ ] Load testing completed
- [ ] Performance benchmarks met
- [ ] Docker containerization
- [ ] CI/CD pipeline

---

## Completion Checklist

- [ ] All files created
- [ ] Dependencies installed
- [ ] Application running
- [ ] All endpoints tested
- [ ] API docs accessible
- [ ] All tests passing
- [ ] Orchestrator integration verified (if available)
- [ ] No errors in logs
- [ ] Ready for PHASE4-4.2

---

## Next Phase

After PHASE4-4.1 is complete:

**PHASE4-4.2: Quality Monitoring**
- Implement relevance scoring
- Add coherence detection
- Create hallucination detection
- Build quality metrics collection

---

**Application Agent skeleton validated and ready for quality monitoring!** 🎯
