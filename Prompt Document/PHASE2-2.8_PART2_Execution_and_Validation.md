# PHASE2-2.8 PART2: REST APIs - Execution and Validation Plan

**Phase**: PHASE2-2.8  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate REST API endpoints  
**Estimated Time**: 15 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for completing and consolidating all REST API endpoints with comprehensive error handling, validation, and documentation.

---

## Execution Strategy

### Approach
1. **Error Handling**: Standardized error responses
2. **Validation**: Request validation and error details
3. **Utility Endpoints**: Additional helpful endpoints
4. **Documentation**: Complete OpenAPI/Swagger docs
5. **Testing**: Comprehensive API tests

### Priority Order
1. **Error Models** (High Priority)
   - Standardized error response format
   
2. **Error Handlers** (High Priority)
   - Global exception handlers

3. **Utility Endpoints** (Medium Priority)
   - Metrics history
   - Workflow list
   - Configuration

4. **Documentation** (High Priority)
   - Enhanced OpenAPI docs

5. **Testing** (High Priority)
   - API endpoint tests

---

## Execution Plan

### Phase 1: Error Handling (5 minutes)

#### Task 1.1: Create Error Models
**File**: `src/models/errors.py`

**Models to create**:
- `ErrorDetail` model
- `ErrorResponse` model
- `ValidationErrorResponse` model

#### Task 1.2: Create Error Handlers
**File**: `src/api/error_handlers.py`

**Handlers to create**:
- `validation_exception_handler`
- `general_exception_handler`
- `http_exception_handler`

---

### Phase 2: Utility Endpoints (5 minutes)

#### Task 2.1: Add Metrics History Endpoint
**File**: `src/api/metrics.py`

Add `GET /api/v1/history/{instance_id}` endpoint

#### Task 2.2: Add Workflow List Endpoint
**File**: `src/api/workflows.py`

Add `GET /api/v1/workflows` endpoint

#### Task 2.3: Create Configuration Endpoints
**File**: `src/api/config.py`

Create:
- `GET /api/v1/config` endpoint
- `GET /api/v1/capabilities` endpoint

---

### Phase 3: Update Main App (2 minutes)

#### Task 3.1: Register Error Handlers
**File**: `src/main.py`

Add exception handlers to app

#### Task 3.2: Include Config Router
**File**: `src/main.py`

Add config router to app

#### Task 3.3: Enhance OpenAPI Documentation
**File**: `src/main.py`

Update FastAPI app description and tags

---

### Phase 4: Testing (3 minutes)

#### Task 4.1: Create Error Handler Tests
**File**: `tests/test_error_handlers.py`

#### Task 4.2: Create Config API Tests
**File**: `tests/test_config_api.py`

#### Task 4.3: Update Existing Tests
Ensure all tests still pass

---

## Validation Plan

### Step 1: Unit Tests

```bash
# Run new tests
pytest tests/test_error_handlers.py -v
pytest tests/test_config_api.py -v

# Run all tests
pytest tests/ -v
```

---

### Step 2: Manual API Testing

#### 2.1 Test Error Handling

**Invalid Request (Validation Error)**:
```bash
curl -X POST http://localhost:8002/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "",
    "instance_type": "invalid_type"
  }'
```

**Expected Response** (422):
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [
    {
      "field": "instance_id",
      "message": "ensure this value has at least 1 character",
      "type": "value_error"
    },
    {
      "field": "instance_type",
      "message": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ],
  "invalid_fields": ["instance_id", "instance_type"],
  "timestamp": "2025-01-24T...",
  "path": "/api/v1/workflows"
}
```

---

#### 2.2 Test Metrics History Endpoint

```bash
curl http://localhost:8002/api/v1/history/localhost:8000?hours=24&limit=100
```

**Expected Response** (200):
```json
[]
```

---

#### 2.3 Test Workflow List Endpoint

```bash
# List all workflows
curl http://localhost:8002/api/v1/workflows

# Filter by status
curl http://localhost:8002/api/v1/workflows?status=completed&limit=10
```

**Expected Response** (200):
```json
[
  {
    "workflow_id": "abc-123",
    "instance_id": "localhost:8000",
    "instance_type": "vllm",
    "status": "completed",
    "created_at": "2025-01-24T...",
    "final_health_score": 95.0
  }
]
```

---

#### 2.4 Test Configuration Endpoints

**Get Configuration**:
```bash
curl http://localhost:8002/api/v1/config
```

**Expected Response** (200):
```json
{
  "agent_name": "performance-agent",
  "agent_type": "performance",
  "port": 8002,
  "log_level": "INFO",
  "environment": "development",
  "version": "0.1.0"
}
```

**Get Capabilities**:
```bash
curl http://localhost:8002/api/v1/capabilities
```

**Expected Response** (200):
```json
{
  "capabilities": [
    "performance_monitoring",
    "bottleneck_detection",
    "slo_monitoring",
    "optimization_recommendations",
    "gradual_rollout",
    "automatic_rollback"
  ],
  "supported_platforms": ["vllm", "tgi", "sglang"],
  "optimization_types": ["kv_cache", "quantization", "batching"],
  "workflow_features": [
    "gradual_rollout",
    "health_monitoring",
    "automatic_rollback",
    "human_approval"
  ]
}
```

---

#### 2.5 Test OpenAPI Documentation

**Access Swagger UI**:
```bash
# Open in browser
start http://localhost:8002/docs

# Or access OpenAPI JSON
curl http://localhost:8002/openapi.json | jq
```

**Verify**:
- ✅ All 17 endpoints listed
- ✅ Request/response schemas documented
- ✅ Error responses documented
- ✅ Tags properly organized
- ✅ Descriptions clear and complete

---

### Step 3: Integration Testing

#### 3.1 Test Complete API Flow

```bash
# 1. Check health
curl http://localhost:8002/api/v1/health

# 2. Get capabilities
curl http://localhost:8002/api/v1/capabilities

# 3. Collect metrics
curl -X POST http://localhost:8002/api/v1/collect/vllm \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "endpoint": "http://localhost:8000/metrics"
  }'

# 4. Analyze performance
curl -X POST http://localhost:8002/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm"
  }'

# 5. Generate optimizations
curl -X POST http://localhost:8002/api/v1/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm"
  }'

# 6. Start workflow
WORKFLOW_ID=$(curl -X POST http://localhost:8002/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "localhost:8000",
    "instance_type": "vllm",
    "requires_approval": false,
    "auto_rollout": true
  }' | jq -r '.workflow_id')

# 7. Get workflow status
curl http://localhost:8002/api/v1/workflows/$WORKFLOW_ID

# 8. List all workflows
curl http://localhost:8002/api/v1/workflows
```

---

## Validation Checklist

### Functional Validation
- [ ] All 17 endpoints functional
- [ ] Error responses standardized
- [ ] Validation errors properly formatted
- [ ] Metrics history endpoint works
- [ ] Workflow list endpoint works
- [ ] Configuration endpoints work
- [ ] OpenAPI documentation complete
- [ ] Swagger UI accessible

### Code Quality
- [ ] All files have proper docstrings
- [ ] Type hints are used throughout
- [ ] Code follows Python best practices
- [ ] No linting errors

### Testing
- [ ] All unit tests pass
- [ ] Test coverage > 80%
- [ ] Integration tests work
- [ ] Manual API tests successful

### Documentation
- [ ] OpenAPI spec complete
- [ ] All endpoints documented
- [ ] Request/response examples provided
- [ ] Error responses documented

---

## Success Metrics

### Test Coverage
- **Target**: > 80% coverage for new code
- **Critical Paths**: 100% coverage
  - Error handlers
  - Validation logic
  - New endpoints

### Performance Metrics
- **Response Time**: < 1 second (except workflows)
- **Error Rate**: < 1%
- **Uptime**: 99.9%

---

## Troubleshooting

### Common Issues

#### Issue 1: Validation Errors Not Formatted
**Symptom**: Validation errors return default FastAPI format

**Solution**:
- Verify error handler is registered
- Check exception handler order
- Ensure `RequestValidationError` is imported

#### Issue 2: OpenAPI Docs Not Updating
**Symptom**: Swagger UI doesn't show new endpoints

**Solution**:
- Restart FastAPI server
- Clear browser cache
- Check router is included in main app

#### Issue 3: Workflow List Returns Empty
**Symptom**: `GET /api/v1/workflows` returns `[]`

**Solution**:
- Start at least one workflow first
- Check workflow_manager.workflows dict
- Verify workflow state conversion

---

## Post-Validation Steps

### After Successful Validation

1. **Run Full Test Suite**:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

2. **Check Coverage**:
```bash
start htmlcov/index.html  # Windows
```

3. **Test All API Endpoints**:
   - ✅ Health endpoints (3)
   - ✅ Metrics endpoints (4)
   - ✅ Analysis endpoint (1)
   - ✅ Optimization endpoint (1)
   - ✅ Workflow endpoints (5)
   - ✅ Config endpoints (2)

4. **Verify OpenAPI Documentation**:
   - ✅ Access http://localhost:8002/docs
   - ✅ Test each endpoint via Swagger UI
   - ✅ Verify request/response schemas

5. **Create Completion Report**

6. **Commit Code**:
```bash
git add .
git commit -m "feat: complete PHASE2-2.8 REST APIs with error handling and documentation"
git push origin main
```

---

## API Documentation Examples

### Example 1: Error Response

**Request**:
```bash
POST /api/v1/workflows
{
  "instance_id": "",
  "instance_type": "invalid"
}
```

**Response** (422):
```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": [
    {
      "field": "instance_id",
      "message": "ensure this value has at least 1 character",
      "type": "value_error"
    }
  ],
  "invalid_fields": ["instance_id"],
  "timestamp": "2025-01-24T12:00:00Z",
  "path": "/api/v1/workflows"
}
```

---

### Example 2: Successful Workflow Creation

**Request**:
```bash
POST /api/v1/workflows
{
  "instance_id": "localhost:8000",
  "instance_type": "vllm",
  "requires_approval": false,
  "auto_rollout": true
}
```

**Response** (201):
```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
  "instance_id": "localhost:8000",
  "instance_type": "vllm",
  "status": "completed",
  "created_at": "2025-01-24T12:00:00Z",
  "updated_at": "2025-01-24T12:15:00Z",
  "rollout_history": [
    {
      "stage": "10%",
      "status": "success",
      "health_score_before": 75.0,
      "health_score_after": 86.25
    },
    {
      "stage": "50%",
      "status": "success",
      "health_score_before": 86.25,
      "health_score_after": 99.19
    },
    {
      "stage": "100%",
      "status": "success",
      "health_score_before": 99.19,
      "health_score_after": 100.0
    }
  ],
  "final_health_score": 100.0,
  "total_improvement": "30-50% overall performance improvement expected"
}
```

---

### Example 3: Configuration Response

**Request**:
```bash
GET /api/v1/config
```

**Response** (200):
```json
{
  "agent_name": "performance-agent",
  "agent_type": "performance",
  "port": 8002,
  "log_level": "INFO",
  "environment": "development",
  "version": "0.1.0"
}
```

---

### Example 4: Capabilities Response

**Request**:
```bash
GET /api/v1/capabilities
```

**Response** (200):
```json
{
  "capabilities": [
    "performance_monitoring",
    "bottleneck_detection",
    "slo_monitoring",
    "optimization_recommendations",
    "gradual_rollout",
    "automatic_rollback"
  ],
  "supported_platforms": ["vllm", "tgi", "sglang"],
  "optimization_types": ["kv_cache", "quantization", "batching"],
  "workflow_features": [
    "gradual_rollout",
    "health_monitoring",
    "automatic_rollback",
    "human_approval"
  ]
}
```

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Error Models | 2 min | Pending |
| Error Handlers | 3 min | Pending |
| Utility Endpoints | 5 min | Pending |
| Update Main App | 2 min | Pending |
| Testing & Validation | 3 min | Pending |
| **Total** | **15 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ Error response models
- ✅ Global error handlers
- ✅ Metrics history endpoint
- ✅ Workflow list endpoint
- ✅ Configuration endpoints
- ✅ Enhanced OpenAPI documentation
- ✅ Comprehensive tests

### Documentation Deliverables
- ✅ Code documentation (docstrings)
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Error response documentation
- ✅ Test documentation

---

## Complete API Reference

### Health & Status (3 endpoints)
1. `GET /api/v1/health` - Basic health check
2. `GET /api/v1/health/detailed` - Detailed health with dependencies
3. `GET /api/v1/health/ready` - Readiness probe

### Metrics (4 endpoints)
4. `POST /api/v1/collect/vllm` - Collect vLLM metrics
5. `POST /api/v1/collect/tgi` - Collect TGI metrics
6. `POST /api/v1/collect/sglang` - Collect SGLang metrics
7. `GET /api/v1/history/{instance_id}` - Get metrics history

### Analysis (1 endpoint)
8. `POST /api/v1/analyze` - Analyze instance performance

### Optimization (1 endpoint)
9. `POST /api/v1/optimize` - Generate optimization plan

### Workflows (5 endpoints)
10. `POST /api/v1/workflows` - Start optimization workflow
11. `GET /api/v1/workflows` - List all workflows
12. `GET /api/v1/workflows/{id}` - Get workflow status
13. `POST /api/v1/workflows/{id}/approve` - Approve workflow
14. `POST /api/v1/workflows/{id}/reject` - Reject workflow

### Configuration (3 endpoints)
15. `GET /api/v1/config` - Get agent configuration
16. `GET /api/v1/capabilities` - Get agent capabilities
17. `GET /metrics` - Prometheus metrics endpoint

**Total**: 17 REST API endpoints

---

## Notes

### Important Considerations
1. **Error Handling**: All errors return standardized format
2. **Validation**: Request validation with detailed error messages
3. **Documentation**: Complete OpenAPI/Swagger documentation
4. **Testing**: Comprehensive test coverage
5. **Performance**: Response time < 1 second (except workflows)

### OpenAPI Features
- **Tags**: Organized by functionality
- **Descriptions**: Clear and comprehensive
- **Examples**: Request/response examples
- **Schemas**: Complete Pydantic models
- **Error Responses**: Documented error formats

---

**Status**: Ready for execution  
**Estimated Completion**: 15 minutes  
**Next Phase**: PHASE2-2.9 - Integration Testing
