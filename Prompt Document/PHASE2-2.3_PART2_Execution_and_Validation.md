# PHASE2-2.3 PART2: TGI Collector - Execution and Validation Plan

**Phase**: PHASE2-2.3  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate TGI metrics collection  
**Estimated Time**: 15 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing the TGI (Text Generation Inference) metrics collector and validating that all components work correctly.

---

## Execution Strategy

### Approach
1. **Leverage Existing Code**: Reuse Prometheus parser from PHASE2-2.2
2. **Similar Structure**: Follow vLLM collector pattern
3. **TGI-Specific**: Focus on TGI-specific metrics
4. **Test-Driven**: Write tests alongside implementation

### Priority Order
1. **TGI Metrics Models** (High Priority)
   - Add TGI-specific Pydantic models
   
2. **TGI Collector** (High Priority)
   - HTTP client for TGI metrics endpoint
   - Metric extraction and processing

3. **API Endpoints** (High Priority)
   - Collection endpoints
   - Error handling

4. **Testing** (High Priority)
   - Unit tests for collector
   - API endpoint tests

---

## Execution Plan

### Phase 1: TGI Metrics Models (3 minutes)

#### Task 1.1: Update Metrics Models
**File**: `src/models/metrics.py`

**Add to existing file**:
- `TGIRequestMetrics` model
- `TGIGenerationMetrics` model
- `TGIMetricsSnapshot` model

**Validation**:
```python
from src.models.metrics import TGIMetricsSnapshot
snapshot = TGIMetricsSnapshot(
    instance_id="test",
    endpoint="http://test",
    request_metrics={},
    generation_metrics={}
)
print(snapshot.model_dump_json())
```

---

### Phase 2: TGI Collector (5 minutes)

#### Task 2.1: Create TGI Collector
**File**: `src/collectors/tgi_collector.py`

**Components**:
- `TGICollector` class
- Async context manager
- `collect()` method
- Metric extraction methods:
  - `_extract_request_metrics()`
  - `_extract_generation_metrics()`

**Similar to vLLM collector but with TGI metrics**

---

### Phase 3: API Endpoints (2 minutes)

#### Task 3.1: Update Metrics API
**File**: `src/api/metrics.py`

**Add Endpoints**:
- `POST /api/v1/collect/tgi` - Collect TGI metrics
- `GET /api/v1/metrics/tgi/{instance_id}` - Get TGI metrics

**Add Import**:
```python
from src.collectors.tgi_collector import TGICollector
from src.models.metrics import TGIMetricsSnapshot
```

---

### Phase 4: Testing (5 minutes)

#### Task 4.1: Create TGI Collector Tests
**File**: `tests/test_tgi_collector.py`

**Test Cases**:
- Successful collection
- HTTP error handling
- Request metrics extraction
- Generation metrics extraction

#### Task 4.2: Create TGI API Tests
**File**: `tests/test_tgi_api.py`

**Test Cases**:
- Successful collection via API
- Failed collection via API

**Run Tests**:
```bash
pytest tests/test_tgi_collector.py -v
pytest tests/test_tgi_api.py -v
```

---

## Validation Plan

### Step 1: Unit Tests

```bash
# Run TGI tests
pytest tests/test_tgi_collector.py -v
pytest tests/test_tgi_api.py -v

# Run all tests
pytest tests/ -v

# Expected output
tests/test_tgi_collector.py::test_collect_tgi_metrics PASSED
tests/test_tgi_collector.py::test_collect_tgi_metrics_error PASSED
tests/test_tgi_collector.py::test_extract_request_metrics PASSED
tests/test_tgi_collector.py::test_extract_generation_metrics PASSED
tests/test_tgi_api.py::test_collect_tgi_metrics_success PASSED
tests/test_tgi_api.py::test_collect_tgi_metrics_failure PASSED

6 new tests passed
```

---

### Step 2: Manual API Testing

#### 2.1 Start Application
```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\performance-agent
python src/main.py
```

#### 2.2 Test TGI Collection

**Create Mock TGI Server** (Optional):
```python
# mock_tgi_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/metrics")
def metrics():
    return """
tgi_request_success_total 250
tgi_request_failure_total 3
tgi_request_count 253
tgi_queue_size 5
tgi_request_mean_time_per_token_duration_seconds 0.015
tgi_request_validation_duration_seconds 0.002
tgi_request_queue_duration_seconds 0.050
tgi_request_inference_duration_seconds 1.2
tgi_request_input_length 128
tgi_request_generated_tokens 256
tgi_request_generated_tokens_total 64000
tgi_request_max_new_tokens 512
tgi_batch_current_size 8
tgi_batch_current_max_tokens 2048
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

**Test Collection Endpoint**:
```bash
curl -X POST http://localhost:8002/api/v1/collect/tgi \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "tgi-001",
    "endpoint": "http://localhost:8080/metrics",
    "timeout": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "instance_id": "tgi-001",
  "timestamp": "2025-01-24T...",
  "metrics": {
    "timestamp": "2025-01-24T...",
    "instance_id": "tgi-001",
    "endpoint": "http://localhost:8080/metrics",
    "request_metrics": {
      "success_total": 250,
      "failure_total": 3,
      "request_count": 253,
      "queue_size": 5,
      "mean_time_per_token_seconds": 0.015,
      "validation_duration_seconds": 0.002,
      "queue_duration_seconds": 0.050,
      "inference_duration_seconds": 1.2
    },
    "generation_metrics": {
      "input_length": 128,
      "generated_tokens": 256,
      "generated_tokens_total": 64000,
      "max_new_tokens": 512,
      "batch_current_size": 8,
      "batch_current_max_tokens": 2048
    },
    "raw_metrics": [...]
  }
}
```

#### 2.3 Test GET Endpoint

```bash
curl "http://localhost:8002/api/v1/metrics/tgi/tgi-001?endpoint=http://localhost:8080/metrics"
```

---

### Step 3: Integration Testing

#### 3.1 Test with Real TGI (If Available)

If you have a TGI instance running:

```bash
# Assuming TGI is running on localhost:8080
curl -X POST http://localhost:8002/api/v1/collect/tgi \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "tgi-production",
    "endpoint": "http://localhost:8080/metrics",
    "timeout": 10
  }'
```

---

### Step 4: Error Handling Testing

#### 4.1 Test Invalid Endpoint

```bash
curl -X POST http://localhost:8002/api/v1/collect/tgi \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "tgi-invalid",
    "endpoint": "http://invalid-host:8080/metrics",
    "timeout": 5
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "instance_id": "tgi-invalid",
  "timestamp": "2025-01-24T...",
  "metrics": null,
  "error": "Connection error message..."
}
```

---

## Validation Checklist

### Functional Validation
- [ ] TGI collector fetches metrics via HTTP
- [ ] Collector extracts request metrics
- [ ] Collector extracts generation metrics
- [ ] API endpoint accepts collection requests
- [ ] API endpoint returns proper responses
- [ ] Error handling works correctly

### Code Quality
- [ ] All files have proper docstrings
- [ ] Type hints are used throughout
- [ ] Code follows Python best practices
- [ ] No linting errors
- [ ] Async/await used correctly

### Testing
- [ ] All unit tests pass
- [ ] Test coverage > 80%
- [ ] Tests cover error cases
- [ ] Tests use proper mocking

### Performance
- [ ] Collection completes within timeout
- [ ] No memory leaks in async operations

---

## Success Metrics

### Test Coverage
- **Target**: > 80% coverage for new code
- **Critical Paths**: 100% coverage
  - TGI collector
  - Metric extraction
  - API endpoints

### Performance Metrics
- **Collection Time**: < 5 seconds
- **Memory Usage**: < 50 MB increase

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'src.collectors.tgi_collector'`

**Solution**:
```bash
# Verify file exists
ls src/collectors/tgi_collector.py
```

#### Issue 2: TGI Metrics Not Found
**Symptom**: Metrics extraction returns zeros

**Solution**:
- Check TGI metrics format
- Verify metric names match TGI version
- Add debug logging

#### Issue 3: HTTP Connection Errors
**Symptom**: `httpx.ConnectError`

**Solution**:
- Verify endpoint URL
- Check if TGI is running
- Increase timeout

---

## Post-Validation Steps

### After Successful Validation

1. **Run Full Test Suite**:
```bash
pytest tests/ -v --cov=src --cov-report=html
```

2. **Check Coverage**:
```bash
# Open coverage report
start htmlcov/index.html  # Windows
```

3. **Create Completion Report**:
- Document test results
- Document any issues
- Document performance metrics

4. **Commit Code**:
```bash
git add .
git commit -m "feat: implement PHASE2-2.3 TGI metrics collector"
git push origin main
```

---

## Next Steps

### Immediate
1. ✅ Validate all functionality
2. ✅ Run complete test suite
3. ✅ Create completion report
4. ✅ Commit and push code

### Next Phase: PHASE2-2.4
**SGLang Collector**: Implement metrics collection for SGLang
- SGLang Prometheus metrics
- SGLang-specific performance indicators
- Integration with Performance Agent

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| TGI Metrics Models | 3 min | Pending |
| TGI Collector | 5 min | Pending |
| API Endpoints | 2 min | Pending |
| Testing & Validation | 5 min | Pending |
| **Total** | **15 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ TGI metrics models (Pydantic)
- ✅ TGI collector
- ✅ API endpoints
- ✅ Comprehensive tests

### Documentation Deliverables
- ✅ Code documentation (docstrings)
- ✅ API documentation (OpenAPI)
- ✅ Test documentation

---

## Notes

### Important Considerations
1. **Async Operations**: All HTTP operations must be async
2. **Error Handling**: Graceful handling of network errors
3. **Timeout**: Configurable timeout for slow endpoints
4. **Parsing**: Reuse Prometheus parser from PHASE2-2.2
5. **Testing**: Mock HTTP responses for unit tests

### TGI Metrics Reference
- **Documentation**: https://huggingface.co/docs/text-generation-inference
- **Endpoint**: Usually `http://host:port/metrics`
- **Format**: Prometheus text format
- **Update Frequency**: Real-time

---

**Status**: Ready for execution  
**Estimated Completion**: 15 minutes  
**Next Phase**: PHASE2-2.4 - SGLang Collector
