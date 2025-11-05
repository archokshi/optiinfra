# PHASE2-2.1 PART2: Performance Agent Skeleton - Execution and Validation Plan

**Phase**: PHASE2-2.1  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate the skeleton  
**Estimated Time**: 10 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing the Performance Agent skeleton and validating that all components work correctly.

---

## Execution Strategy

### Approach
1. **Sequential Implementation**: Create files in logical order
2. **Incremental Testing**: Test each component as it's built
3. **Validation**: Verify all endpoints and registration work

### Priority Order
1. **Core Setup** (High Priority)
   - Project structure
   - Configuration
   - Logging

2. **API Layer** (High Priority)
   - Health endpoints
   - Models

3. **Orchestrator Integration** (High Priority)
   - Registration client
   - Heartbeat mechanism

4. **Infrastructure** (Medium Priority)
   - Docker setup
   - Testing framework

---

## Execution Plan

### Phase 1: Project Setup (3 minutes)

#### Task 1.1: Create Directory Structure
```bash
# Navigate to services directory
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services

# Create performance-agent directory
mkdir performance-agent
cd performance-agent

# Create subdirectories
mkdir -p src\api src\core src\models src\middleware tests
```

#### Task 1.2: Create Configuration Files
```bash
# Create .env.example
# Create requirements.txt
# Create pytest.ini
# Create .gitignore
```

**Files to Create**:
- `.env.example`
- `requirements.txt`
- `pytest.ini`
- `.gitignore`

---

### Phase 2: Core Implementation (4 minutes)

#### Task 2.1: Configuration Management
**File**: `src/config.py`
- Implement Settings class with Pydantic
- Define all configuration parameters
- Load from environment variables

#### Task 2.2: Logging Setup
**File**: `src/core/logger.py`
- Implement JSONFormatter
- Configure structured logging
- Set appropriate log levels

#### Task 2.3: Health Models
**File**: `src/models/health.py`
- Define HealthResponse model
- Define DetailedHealthResponse model
- Define ServiceInfo model

#### Task 2.4: Health Endpoints
**File**: `src/api/health.py`
- Implement `/health` endpoint
- Implement `/health/detailed` endpoint
- Implement `/` service info endpoint

---

### Phase 3: Orchestrator Integration (2 minutes)

#### Task 3.1: Registration Client
**File**: `src/core/registration.py`
- Implement OrchestratorClient class
- Implement registration logic
- Implement heartbeat mechanism
- Handle connection errors gracefully

---

### Phase 4: Main Application (1 minute)

#### Task 4.1: FastAPI Application
**File**: `src/main.py`
- Initialize FastAPI app
- Add CORS middleware
- Include health router
- Add Prometheus metrics endpoint
- Implement startup/shutdown events

---

### Phase 5: Docker & Testing (2 minutes)

#### Task 5.1: Docker Configuration
**Files**: `Dockerfile`, `docker-compose.yml`
- Create Dockerfile for containerization
- Create docker-compose.yml with dependencies

#### Task 5.2: Testing Framework
**Files**: `tests/conftest.py`, `tests/test_health.py`
- Set up pytest configuration
- Create test fixtures
- Implement health endpoint tests

#### Task 5.3: Documentation
**File**: `README.md`
- Document setup instructions
- Document API endpoints
- Document configuration options

---

## Validation Plan

### Step 1: Local Testing

#### 1.1 Install Dependencies
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 1.2 Run Application
```bash
# Start the application
python src/main.py

# Or with uvicorn
uvicorn src.main:app --reload --port 8002
```

#### 1.3 Test Endpoints
```bash
# Test health check
curl http://localhost:8002/api/v1/health

# Test detailed health
curl http://localhost:8002/api/v1/health/detailed

# Test service info
curl http://localhost:8002/api/v1/

# Test metrics
curl http://localhost:8002/metrics
```

**Expected Responses**:
```json
// GET /api/v1/health
{
  "status": "healthy",
  "timestamp": "2025-01-23T...",
  "version": "0.1.0",
  "agent_id": "performance-agent-001",
  "agent_type": "performance",
  "uptime_seconds": 10.5
}

// GET /api/v1/health/detailed
{
  "status": "healthy",
  "timestamp": "2025-01-23T...",
  "version": "0.1.0",
  "agent_id": "performance-agent-001",
  "agent_type": "performance",
  "uptime_seconds": 10.5,
  "components": {
    "database": {"status": "healthy", "latency_ms": 5.2},
    "cache": {"status": "healthy", "latency_ms": 1.1},
    "orchestrator": {"status": "healthy", "latency_ms": 10.5}
  }
}

// GET /api/v1/
{
  "service": "OptiInfra Performance Agent",
  "version": "0.1.0",
  "status": "running",
  "capabilities": [
    "performance_monitoring",
    "bottleneck_detection",
    "kv_cache_optimization",
    "quantization_optimization",
    "batch_size_tuning"
  ]
}
```

---

### Step 2: Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test
pytest tests/test_health.py -v
```

**Expected Output**:
```
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_detailed_health_check PASSED
tests/test_health.py::test_service_info PASSED

---------- coverage: platform win32, python 3.11.x -----------
Name                          Stmts   Miss  Cover
-------------------------------------------------
src/__init__.py                   0      0   100%
src/api/__init__.py               0      0   100%
src/api/health.py                25      0   100%
src/config.py                    30      0   100%
src/core/__init__.py              0      0   100%
src/core/logger.py               20      2    90%
src/core/registration.py         60     30    50%
src/main.py                      35     10    71%
src/models/__init__.py            0      0   100%
src/models/health.py             15      0   100%
-------------------------------------------------
TOTAL                           185     42    77%

3 passed in 0.5s
```

---

### Step 3: Docker Testing

```bash
# Build and start with docker-compose
docker-compose up -d

# Check logs
docker-compose logs -f performance-agent

# Test endpoints
curl http://localhost:8002/api/v1/health

# Stop containers
docker-compose down
```

---

### Step 4: Orchestrator Registration Testing

**Note**: This requires the orchestrator to be running. If orchestrator is not available, the agent should handle the failure gracefully.

#### 4.1 With Orchestrator Running
```bash
# Start orchestrator (from orchestrator directory)
# Then start performance agent
python src/main.py
```

**Expected Log Output**:
```json
{
  "timestamp": "2025-01-23T...",
  "level": "INFO",
  "logger": "src.core.registration",
  "message": "Successfully registered with orchestrator",
  "agent_id": "performance-agent-001",
  "orchestrator_url": "http://localhost:8080"
}
```

#### 4.2 Without Orchestrator (Graceful Failure)
```bash
# Start performance agent without orchestrator
python src/main.py
```

**Expected Log Output**:
```json
{
  "timestamp": "2025-01-23T...",
  "level": "ERROR",
  "logger": "src.core.registration",
  "message": "Error registering with orchestrator: ...",
  "agent_id": "performance-agent-001"
}
```

**Agent should still start and be functional** even if orchestrator is unavailable.

---

## Validation Checklist

### Functional Validation
- [ ] Application starts without errors
- [ ] Health check endpoint returns 200 OK
- [ ] Detailed health check returns component status
- [ ] Service info endpoint returns capabilities
- [ ] Metrics endpoint returns Prometheus metrics
- [ ] Logging outputs structured JSON
- [ ] Configuration loads from environment variables

### Orchestrator Integration
- [ ] Registration attempt is made on startup
- [ ] Registration payload is correct
- [ ] Heartbeat loop starts after registration
- [ ] Graceful failure if orchestrator unavailable
- [ ] Heartbeat stops on shutdown

### Code Quality
- [ ] All files have proper docstrings
- [ ] Type hints are used throughout
- [ ] Code follows PEP 8 style guide
- [ ] No linting errors (flake8)
- [ ] Type checking passes (mypy)

### Testing
- [ ] All tests pass
- [ ] Test coverage > 75%
- [ ] Tests are well-documented
- [ ] Test fixtures are reusable

### Docker
- [ ] Dockerfile builds successfully
- [ ] Container starts without errors
- [ ] docker-compose.yml works correctly
- [ ] Environment variables are passed correctly
- [ ] Ports are exposed correctly

### Documentation
- [ ] README.md is complete
- [ ] Setup instructions are clear
- [ ] API endpoints are documented
- [ ] Configuration options are documented

---

## Success Metrics

### Performance Metrics
- **Startup Time**: < 5 seconds
- **Health Check Response**: < 100ms
- **Memory Usage**: < 100 MB
- **CPU Usage**: < 5% idle

### Quality Metrics
- **Test Coverage**: > 75%
- **All Tests Passing**: 100%
- **No Linting Errors**: 0 errors
- **Type Checking**: 100% pass

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'src'`

**Solution**:
```bash
# Ensure you're in the correct directory
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\performance-agent

# Install in development mode
pip install -e .
```

#### Issue 2: Port Already in Use
**Symptom**: `Address already in use: 8002`

**Solution**:
```bash
# Change port in .env
PORT=8003

# Or kill existing process
# Windows:
netstat -ano | findstr :8002
taskkill /PID <pid> /F
```

#### Issue 3: Database Connection Error
**Symptom**: `Connection refused: postgresql://...`

**Solution**:
```bash
# Start PostgreSQL with docker
docker run -d --name perf-postgres \
  -e POSTGRES_DB=performance_agent \
  -e POSTGRES_USER=perf_user \
  -e POSTGRES_PASSWORD=perf_password \
  -p 5433:5432 \
  postgres:14
```

#### Issue 4: Orchestrator Registration Fails
**Symptom**: `Error registering with orchestrator`

**Solution**:
- This is expected if orchestrator is not running
- Agent should still function normally
- Check orchestrator URL in .env
- Verify orchestrator is running and accessible

---

## Post-Validation Steps

### After Successful Validation

1. **Commit Code**:
```bash
git add .
git commit -m "feat: implement PHASE2-2.1 Performance Agent skeleton"
git push origin main
```

2. **Create Validation Report**:
- Document test results
- Document any issues encountered
- Document performance metrics

3. **Update Project Status**:
- Mark PHASE2-2.1 as complete
- Update project documentation
- Plan next phase (PHASE2-2.2)

---

## Next Steps

### Immediate
1. ✅ Validate all functionality
2. ✅ Run complete test suite
3. ✅ Create validation report
4. ✅ Commit and push code

### Next Phase: PHASE2-2.2
**Metrics Collection**: Implement performance metrics collection from vLLM/TGI/SGLang
- Prometheus metrics collection
- vLLM metrics integration
- TGI metrics integration
- SGLang metrics integration

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Project Setup | 3 min | Pending |
| Core Implementation | 4 min | Pending |
| Orchestrator Integration | 2 min | Pending |
| Main Application | 1 min | Pending |
| Docker & Testing | 2 min | Pending |
| **Total** | **12 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ Complete FastAPI application
- ✅ Health check endpoints
- ✅ Orchestrator registration
- ✅ Configuration management
- ✅ Logging setup
- ✅ Docker configuration
- ✅ Test suite

### Documentation Deliverables
- ✅ README.md
- ✅ Code documentation (docstrings)
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Configuration documentation

---

## Notes

### Important Considerations
1. **Graceful Degradation**: Agent should work even if orchestrator is unavailable
2. **Structured Logging**: All logs should be JSON-formatted for easy parsing
3. **Type Safety**: Use type hints throughout for better IDE support
4. **Testing**: Maintain >75% test coverage
5. **Docker**: Ensure containerization works for deployment

### Dependencies
- Requires shared utilities from PHASE1 (0.5, 0.6, 0.10)
- Orchestrator should be running for full functionality
- PostgreSQL and Redis for data storage (optional for skeleton)

---

**Status**: Ready for execution  
**Estimated Completion**: 10 minutes  
**Next Phase**: PHASE2-2.2 - Metrics Collection
