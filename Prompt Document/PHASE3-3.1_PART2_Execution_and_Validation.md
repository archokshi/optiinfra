# PHASE3-3.1 PART2: Resource Agent Skeleton - Execution and Validation

**Phase**: PHASE3-3.1  
**Agent**: Resource Agent  
**Objective**: Execute implementation and validate the skeleton  
**Estimated Time**: 20 minutes  
**Prerequisites**: PART1 completed

---

## Execution Steps

### Step 1: Create Project Structure (2 minutes)

```bash
# Navigate to services directory
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services

# Create resource-agent directory structure
mkdir -p resource-agent/src/{api,core,models,middleware}
mkdir -p resource-agent/tests

# Navigate to resource-agent
cd resource-agent
```

---

### Step 2: Create Core Files (5 minutes)

Execute the following in order:

1. **Create requirements.txt**
2. **Create .env.example**
3. **Create src/config.py**
4. **Create src/core/logger.py**
5. **Create src/models/health.py**
6. **Create src/models/metrics.py**

Verify each file is created successfully before proceeding.

---

### Step 3: Create API Endpoints (3 minutes)

1. **Create src/api/__init__.py** (empty)
2. **Create src/api/health.py**
3. **Create src/core/registration.py**

---

### Step 4: Create Main Application (2 minutes)

1. **Create src/__init__.py** (empty)
2. **Create src/main.py**

---

### Step 5: Create Tests (3 minutes)

1. **Create tests/__init__.py** (empty)
2. **Create tests/conftest.py**
3. **Create tests/test_health.py**
4. **Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --cov=src
    --cov-report=html
    --cov-report=term-missing
```

---

### Step 6: Create Docker Files (2 minutes)

1. **Create Dockerfile**
2. **Create docker-compose.yml**
3. **Create .gitignore**

```gitignore
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

# Logs
*.log

# Database
*.db
*.sqlite3
```

---

### Step 7: Create Documentation (2 minutes)

1. **Create README.md**

---

## Validation Steps

### Step 8: Install Dependencies (2 minutes)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Expected Output:**
```
Successfully installed fastapi-0.104.1 uvicorn-0.24.0 ...
```

---

### Step 9: Run Tests (2 minutes)

```bash
pytest tests/ -v --cov=src
```

**Expected Output:**
```
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_detailed_health_check PASSED
tests/test_health.py::test_readiness_check PASSED
tests/test_health.py::test_liveness_check PASSED
tests/test_health.py::test_root_endpoint PASSED

---------- coverage: platform win32, python 3.11.x -----------
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/__init__.py                   0      0   100%
src/api/__init__.py               0      0   100%
src/api/health.py                42      0   100%
src/config.py                    25      0   100%
src/core/__init__.py              0      0   100%
src/core/logger.py               20      0   100%
src/core/registration.py         65     45    31%   (heartbeat not tested)
src/main.py                      35     15    57%   (startup/shutdown not tested)
src/models/__init__.py            0      0   100%
src/models/health.py             15      0   100%
src/models/metrics.py            35      0   100%
-----------------------------------------------------------
TOTAL                           237    60    75%

========== 5 passed in 2.34s ==========
```

---

### Step 10: Start Application (2 minutes)

```bash
# Start the application
uvicorn src.main:app --reload --port 8003
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\...\\resource-agent']
INFO:     Uvicorn running on http://127.0.0.1:8003 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
2025-10-24 21:00:00 - resource_agent - INFO - Starting Resource Agent: resource-agent-001
2025-10-24 21:00:00 - resource_agent - INFO - Environment: development
2025-10-24 21:00:00 - resource_agent - INFO - Port: 8003
2025-10-24 21:00:00 - resource_agent.registration - INFO - Successfully registered with orchestrator: resource-agent-001
INFO:     Application startup complete.
```

---

### Step 11: Test Endpoints (3 minutes)

Open a new terminal and test the endpoints:

#### Test 1: Root Endpoint
```bash
curl http://localhost:8003/
```

**Expected Response:**
```json
{
  "agent": "Resource Agent",
  "version": "1.0.0",
  "status": "active",
  "agent_id": "resource-agent-001"
}
```

#### Test 2: Health Check
```bash
curl http://localhost:8003/health/
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T21:00:00.000000",
  "agent_id": "resource-agent-001",
  "agent_type": "resource",
  "version": "1.0.0",
  "uptime_seconds": 123.45
}
```

#### Test 3: Detailed Health Check
```bash
curl http://localhost:8003/health/detailed
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-24T21:00:00.000000",
  "agent_id": "resource-agent-001",
  "agent_type": "resource",
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "nvidia_smi": "healthy",
    "orchestrator": "healthy"
  },
  "metrics": {
    "uptime_seconds": 123.45,
    "memory_usage_mb": 0.0,
    "cpu_usage_percent": 0.0
  }
}
```

#### Test 4: Readiness Check
```bash
curl http://localhost:8003/health/ready
```

**Expected Response:**
```json
{
  "ready": true
}
```

#### Test 5: Liveness Check
```bash
curl http://localhost:8003/health/live
```

**Expected Response:**
```json
{
  "alive": true
}
```

#### Test 6: API Documentation
Open browser and navigate to:
- Swagger UI: http://localhost:8003/docs
- ReDoc: http://localhost:8003/redoc

---

### Step 12: Docker Validation (Optional - 3 minutes)

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f resource-agent

# Test endpoint
curl http://localhost:8003/health/

# Stop services
docker-compose down
```

**Expected Output:**
```
Creating network "resource-agent_default" with the default driver
Creating resource-agent_postgres_1 ... done
Creating resource-agent_redis_1    ... done
Creating resource-agent_resource-agent_1 ... done
```

---

## Validation Checklist

### Functionality Tests

- [ ] **Application Starts**: `uvicorn src.main:app` runs without errors
- [ ] **Root Endpoint**: GET `/` returns agent info
- [ ] **Health Check**: GET `/health/` returns healthy status
- [ ] **Detailed Health**: GET `/health/detailed` returns component status
- [ ] **Readiness**: GET `/health/ready` returns ready status
- [ ] **Liveness**: GET `/health/live` returns alive status
- [ ] **API Docs**: Swagger UI accessible at `/docs`

### Code Quality Tests

- [ ] **All Tests Pass**: `pytest tests/ -v` shows 5/5 passing
- [ ] **Code Coverage**: Coverage > 70%
- [ ] **No Linting Errors**: Code follows PEP 8
- [ ] **Type Hints**: All functions have type hints

### Integration Tests

- [ ] **Orchestrator Registration**: Agent registers successfully (if orchestrator running)
- [ ] **Heartbeat**: Periodic heartbeat sent to orchestrator
- [ ] **Graceful Shutdown**: Agent deregisters on shutdown

### Docker Tests

- [ ] **Docker Build**: `docker-compose build` succeeds
- [ ] **Container Start**: `docker-compose up` starts all services
- [ ] **Health Check**: Container health check passes
- [ ] **GPU Access**: Container can access NVIDIA GPU (if available)

---

## Troubleshooting

### Issue: Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in the resource-agent directory
cd resource-agent

# Run with Python module syntax
python -m pytest tests/
```

---

### Issue: Port Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8003
# Windows:
netstat -ano | findstr :8003
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8003
kill -9 <PID>
```

---

### Issue: Orchestrator Connection Failed

**Problem**: `Failed to register with orchestrator`

**Solution**:
- This is expected if orchestrator is not running
- Agent will continue to function without orchestrator
- Heartbeat will retry periodically

---

### Issue: NVIDIA Driver Not Found

**Problem**: `nvidia-ml-py` fails to initialize

**Solution**:
- This is expected if no NVIDIA GPU is present
- GPU metrics collection will be skipped
- Agent will still collect CPU/memory metrics

---

## Performance Metrics

### Expected Performance

- **Startup Time**: < 2 seconds
- **Health Check Response**: < 50ms
- **Memory Usage**: < 100MB
- **CPU Usage (idle)**: < 5%

### Benchmark Commands

```bash
# Response time test
time curl http://localhost:8003/health/

# Load test (requires apache-bench)
ab -n 1000 -c 10 http://localhost:8003/health/
```

**Expected ab Output:**
```
Requests per second:    500+ [#/sec]
Time per request:       20ms [mean]
```

---

## Success Criteria

### Must Have ✅

- [x] FastAPI application starts successfully
- [x] All health endpoints return 200 OK
- [x] All unit tests pass (5/5)
- [x] Code coverage > 70%
- [x] API documentation accessible
- [x] Orchestrator registration works (or gracefully fails)

### Nice to Have 🎯

- [ ] Docker container builds and runs
- [ ] GPU metrics collection works (if GPU available)
- [ ] Load test shows > 500 req/sec
- [ ] Memory usage < 100MB

---

## Next Phase Preview

**PHASE3-3.2: GPU Collector**

What we'll build:
- nvidia-smi integration
- Real-time GPU metrics collection
- GPU utilization analysis
- Multi-GPU support
- Metrics storage in ClickHouse

**Estimated Time**: 25+20m (45 minutes)

---

## Completion Summary

After completing this phase, you will have:

1. ✅ **Fully Functional Resource Agent Skeleton**
   - FastAPI application running
   - Health checks operational
   - Orchestrator integration ready

2. ✅ **Test Coverage**
   - 5 unit tests passing
   - 75%+ code coverage
   - CI/CD ready

3. ✅ **Production Ready Infrastructure**
   - Docker support
   - Environment configuration
   - Logging and monitoring

4. ✅ **Documentation**
   - README with setup instructions
   - API documentation auto-generated
   - Troubleshooting guide

---

**Resource Agent skeleton is ready! Let's move to GPU metrics collection.** 🚀
