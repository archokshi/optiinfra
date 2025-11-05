# PHASE2-2.4 PART2: SGLang Collector - Execution and Validation Plan

**Phase**: PHASE2-2.4  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate SGLang metrics collection  
**Estimated Time**: 15 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing the SGLang metrics collector and validating that all components work correctly.

---

## Execution Strategy

### Approach
1. **Leverage Existing Code**: Reuse Prometheus parser from PHASE2-2.2
2. **Similar Structure**: Follow vLLM and TGI collector patterns
3. **SGLang-Specific**: Focus on SGLang-specific metrics (RadixAttention, cache)
4. **Test-Driven**: Write tests alongside implementation

### Priority Order
1. **SGLang Metrics Models** (High Priority)
   - Add SGLang-specific Pydantic models
   
2. **SGLang Collector** (High Priority)
   - HTTP client for SGLang metrics endpoint
   - Metric extraction and processing

3. **API Endpoints** (High Priority)
   - Collection endpoints
   - Error handling

4. **Testing** (High Priority)
   - Unit tests for collector
   - API endpoint tests

---

## Execution Plan

### Phase 1: SGLang Metrics Models (3 minutes)

#### Task 1.1: Update Metrics Models
**File**: `src/models/metrics.py`

**Add to existing file**:
- `SGLangRequestMetrics` model
- `SGLangCacheMetrics` model
- `SGLangSystemMetrics` model
- `SGLangMetricsSnapshot` model
- Update `MetricsCollectionResponse` to include SGLang

**Validation**:
```python
from src.models.metrics import SGLangMetricsSnapshot
snapshot = SGLangMetricsSnapshot(
    instance_id="test",
    endpoint="http://test",
    request_metrics={},
    cache_metrics={},
    system_metrics={}
)
print(snapshot.model_dump_json())
```

---

### Phase 2: SGLang Collector (5 minutes)

#### Task 2.1: Create SGLang Collector
**File**: `src/collectors/sglang_collector.py`

**Components**:
- `SGLangCollector` class
- Async context manager
- `collect()` method
- Metric extraction methods:
  - `_extract_request_metrics()`
  - `_extract_cache_metrics()`
  - `_extract_system_metrics()`

**Similar to vLLM/TGI collectors but with SGLang metrics**

---

### Phase 3: API Endpoints (2 minutes)

#### Task 3.1: Update Metrics API
**File**: `src/api/metrics.py`

**Add Endpoints**:
- `POST /api/v1/collect/sglang` - Collect SGLang metrics
- `GET /api/v1/metrics/sglang/{instance_id}` - Get SGLang metrics

**Add Import**:
```python
from src.collectors.sglang_collector import SGLangCollector
from src.models.metrics import SGLangMetricsSnapshot
```

---

### Phase 4: Testing (5 minutes)

#### Task 4.1: Create SGLang Collector Tests
**File**: `tests/test_sglang_collector.py`

**Test Cases**:
- Successful collection
- HTTP error handling
- Request metrics extraction
- Cache metrics extraction
- System metrics extraction

#### Task 4.2: Create SGLang API Tests
**File**: `tests/test_sglang_api.py`

**Test Cases**:
- Successful collection via API
- Failed collection via API

**Run Tests**:
```bash
pytest tests/test_sglang_collector.py -v
pytest tests/test_sglang_api.py -v
```

---

## Validation Plan

### Step 1: Unit Tests

```bash
# Run SGLang tests
pytest tests/test_sglang_collector.py -v
pytest tests/test_sglang_api.py -v

# Run all tests
pytest tests/ -v

# Expected output
tests/test_sglang_collector.py::test_collect_sglang_metrics PASSED
tests/test_sglang_collector.py::test_collect_sglang_metrics_error PASSED
tests/test_sglang_collector.py::test_extract_request_metrics PASSED
tests/test_sglang_collector.py::test_extract_cache_metrics PASSED
tests/test_sglang_collector.py::test_extract_system_metrics PASSED
tests/test_sglang_api.py::test_collect_sglang_metrics_success PASSED
tests/test_sglang_api.py::test_collect_sglang_metrics_failure PASSED

7 new tests passed
```

---

### Step 2: Manual API Testing

#### 2.1 Start Application
```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\performance-agent
python src/main.py
```

#### 2.2 Test SGLang Collection

**Create Mock SGLang Server** (Optional):
```python
# mock_sglang_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/metrics")
def metrics():
    return """
sglang:request_success_total 300
sglang:request_failure_total 2
sglang:request_duration_seconds 1.8
sglang:time_to_first_token_seconds 0.020
sglang:time_per_output_token_seconds 0.008
sglang:request_input_tokens 256
sglang:request_output_tokens 512
sglang:cache_hit_rate 0.85
sglang:cache_memory_usage_bytes 4294967296
sglang:radix_cache_size 1024
sglang:prefix_cache_hit_total 255
sglang:num_requests_running 4
sglang:num_requests_waiting 1
sglang:batch_size_current 16
sglang:throughput_tokens_per_second 1250.5
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=30000)
```

**Test Collection Endpoint**:
```bash
curl -X POST http://localhost:8002/api/v1/collect/sglang \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "sglang-001",
    "endpoint": "http://localhost:30000/metrics",
    "timeout": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "instance_id": "sglang-001",
  "timestamp": "2025-01-24T...",
  "metrics": {
    "timestamp": "2025-01-24T...",
    "instance_id": "sglang-001",
    "endpoint": "http://localhost:30000/metrics",
    "request_metrics": {
      "success_total": 300,
      "failure_total": 2,
      "request_duration_seconds": 1.8,
      "time_to_first_token_seconds": 0.020,
      "time_per_output_token_seconds": 0.008,
      "input_tokens": 256,
      "output_tokens": 512
    },
    "cache_metrics": {
      "cache_hit_rate": 0.85,
      "cache_memory_usage_bytes": 4294967296,
      "radix_cache_size": 1024,
      "prefix_cache_hit_total": 255
    },
    "system_metrics": {
      "num_requests_running": 4,
      "num_requests_waiting": 1,
      "batch_size_current": 16,
      "throughput_tokens_per_second": 1250.5
    },
    "raw_metrics": [...]
  }
}
```

#### 2.3 Test GET Endpoint

```bash
curl "http://localhost:8002/api/v1/metrics/sglang/sglang-001?endpoint=http://localhost:30000/metrics"
```

---

### Step 3: Integration Testing

#### 3.1 Test with Real SGLang (If Available)

If you have a SGLang instance running:

```bash
# Assuming SGLang is running on localhost:30000
curl -X POST http://localhost:8002/api/v1/collect/sglang \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "sglang-production",
    "endpoint": "http://localhost:30000/metrics",
    "timeout": 10
  }'
```

---

### Step 4: Error Handling Testing

#### 4.1 Test Invalid Endpoint

```bash
curl -X POST http://localhost:8002/api/v1/collect/sglang \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "sglang-invalid",
    "endpoint": "http://invalid-host:30000/metrics",
    "timeout": 5
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "instance_id": "sglang-invalid",
  "timestamp": "2025-01-24T...",
  "metrics": null,
  "error": "Connection error message..."
}
```

---

## Validation Checklist

### Functional Validation
- [ ] SGLang collector fetches metrics via HTTP
- [ ] Collector extracts request metrics
- [ ] Collector extracts cache metrics
- [ ] Collector extracts system metrics
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
  - SGLang collector
  - Metric extraction
  - API endpoints

### Performance Metrics
- **Collection Time**: < 5 seconds
- **Memory Usage**: < 50 MB increase

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'src.collectors.sglang_collector'`

**Solution**:
```bash
# Verify file exists
ls src/collectors/sglang_collector.py
```

#### Issue 2: SGLang Metrics Not Found
**Symptom**: Metrics extraction returns zeros

**Solution**:
- Check SGLang metrics format
- Verify metric names match SGLang version
- Add debug logging

#### Issue 3: HTTP Connection Errors
**Symptom**: `httpx.ConnectError`

**Solution**:
- Verify endpoint URL
- Check if SGLang is running
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
git commit -m "feat: implement PHASE2-2.4 SGLang metrics collector"
git push origin main
```

---

## Next Steps

### Immediate
1. ✅ Validate all functionality
2. ✅ Run complete test suite
3. ✅ Create completion report
4. ✅ Commit and push code

### Next Phase: PHASE2-2.5
**Metrics Storage**: Store collected metrics in database
- Database schema for metrics
- Storage service
- Query interface

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| SGLang Metrics Models | 3 min | Pending |
| SGLang Collector | 5 min | Pending |
| API Endpoints | 2 min | Pending |
| Testing & Validation | 5 min | Pending |
| **Total** | **15 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ SGLang metrics models (Pydantic)
- ✅ SGLang collector
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

### SGLang Metrics Reference
- **Documentation**: https://github.com/sgl-project/sglang
- **Endpoint**: Usually `http://host:port/metrics`
- **Format**: Prometheus text format
- **Update Frequency**: Real-time

### SGLang-Specific Features
- **RadixAttention**: Efficient KV cache reuse
- **Prefix Caching**: Cache common prefixes
- **High Cache Hit Rate**: 80-90% typical

---

**Status**: Ready for execution  
**Estimated Completion**: 15 minutes  
**Next Phase**: PHASE2-2.5 - Metrics Storage
