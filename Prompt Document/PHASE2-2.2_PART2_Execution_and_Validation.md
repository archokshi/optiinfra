# PHASE2-2.2 PART2: vLLM Collector - Execution and Validation Plan

**Phase**: PHASE2-2.2  
**Agent**: Performance Agent  
**Objective**: Execute implementation and validate vLLM metrics collection  
**Estimated Time**: 20 minutes  
**Priority**: HIGH

---

## Overview

This document outlines the execution steps for implementing the vLLM metrics collector and validating that all components work correctly with real or mocked vLLM metrics.

---

## Execution Strategy

### Approach
1. **Bottom-Up Implementation**: Start with parser, then collector, then API
2. **Test-Driven**: Write tests alongside implementation
3. **Mock First**: Use mocked metrics for initial testing
4. **Real Integration**: Test with actual vLLM instance if available

### Priority Order
1. **Metrics Models** (High Priority)
   - Pydantic models for all metric types
   
2. **Prometheus Parser** (High Priority)
   - Parse Prometheus text format
   - Extract metrics and labels

3. **vLLM Collector** (High Priority)
   - HTTP client for metrics endpoint
   - Metric extraction and processing

4. **API Endpoints** (High Priority)
   - Collection endpoints
   - Error handling

5. **Testing** (High Priority)
   - Unit tests for all components
   - Integration tests

---

## Execution Plan

### Phase 1: Metrics Models (5 minutes)

#### Task 1.1: Create Metrics Models
**File**: `src/models/metrics.py`

**Models to Create**:
- `MetricType` - Enum for metric types
- `PrometheusMetric` - Single metric
- `VLLMRequestMetrics` - Request metrics
- `VLLMGPUMetrics` - GPU metrics
- `VLLMThroughputMetrics` - Throughput metrics
- `VLLMMetricsSnapshot` - Complete snapshot
- `MetricsCollectionRequest` - API request model
- `MetricsCollectionResponse` - API response model

**Validation**:
```python
# Quick validation
from src.models.metrics import VLLMMetricsSnapshot
snapshot = VLLMMetricsSnapshot(
    instance_id="test",
    endpoint="http://test",
    request_metrics={},
    gpu_metrics={},
    throughput_metrics={}
)
print(snapshot.model_dump_json())
```

---

### Phase 2: Prometheus Parser (7 minutes)

#### Task 2.1: Create Parser
**File**: `src/collectors/prometheus_parser.py`

**Components**:
- Regex patterns for parsing
- `parse()` method for full text
- `_parse_metric_line()` for single line
- `_parse_labels()` for label extraction
- `filter_metrics()` for filtering

#### Task 2.2: Test Parser
**File**: `tests/test_prometheus_parser.py`

**Test Cases**:
- Parse counter metrics
- Parse gauge metrics
- Parse histogram metrics
- Parse labels
- Filter by prefix
- Filter by labels

**Run Tests**:
```bash
pytest tests/test_prometheus_parser.py -v
```

---

### Phase 3: vLLM Collector (5 minutes)

#### Task 3.1: Create Collector
**File**: `src/collectors/vllm_collector.py`

**Components**:
- `VLLMCollector` class
- Async context manager
- `collect()` method
- Metric extraction methods:
  - `_extract_request_metrics()`
  - `_extract_gpu_metrics()`
  - `_extract_throughput_metrics()`

#### Task 3.2: Test Collector
**File**: `tests/test_vllm_collector.py`

**Test Cases**:
- Successful collection
- HTTP error handling
- Metric extraction
- Invalid metrics handling

**Run Tests**:
```bash
pytest tests/test_vllm_collector.py -v
```

---

### Phase 4: API Endpoints (3 minutes)

#### Task 4.1: Create Metrics API
**File**: `src/api/metrics.py`

**Endpoints**:
- `POST /api/v1/collect/vllm` - Collect metrics
- `GET /api/v1/metrics/vllm/{instance_id}` - Get metrics

#### Task 4.2: Update Main App
**File**: `src/main.py`

**Changes**:
```python
from src.api import health, metrics

app.include_router(metrics.router, prefix="/api/v1", tags=["metrics"])
```

#### Task 4.3: Test API
**File**: `tests/test_metrics_api.py`

**Test Cases**:
- Successful collection
- Failed collection
- Error responses

**Run Tests**:
```bash
pytest tests/test_metrics_api.py -v
```

---

## Validation Plan

### Step 1: Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Expected output
tests/test_prometheus_parser.py::test_parse_metrics PASSED
tests/test_prometheus_parser.py::test_parse_counter PASSED
tests/test_prometheus_parser.py::test_parse_gauge PASSED
tests/test_prometheus_parser.py::test_filter_by_prefix PASSED
tests/test_prometheus_parser.py::test_filter_by_labels PASSED
tests/test_vllm_collector.py::test_collect_metrics PASSED
tests/test_vllm_collector.py::test_collect_metrics_error PASSED
tests/test_metrics_api.py::test_collect_vllm_metrics_success PASSED
tests/test_metrics_api.py::test_collect_vllm_metrics_failure PASSED

9 passed
```

---

### Step 2: Manual API Testing

#### 2.1 Start Application
```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\performance-agent
python src/main.py
```

#### 2.2 Test Metrics Collection (Mock)

**Create Mock vLLM Server** (Optional):
```python
# mock_vllm_server.py
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/metrics")
def metrics():
    return """
vllm:request_success_total 150
vllm:request_failure_total 5
vllm:time_to_first_token_seconds 0.025
vllm:time_per_output_token_seconds 0.010
vllm:e2e_request_latency_seconds 1.5
vllm:gpu_cache_usage_perc 75.5
vllm:gpu_memory_usage_bytes 8589934592
vllm:num_requests_running 3
vllm:num_requests_waiting 2
vllm:prompt_tokens_total 15000
vllm:generation_tokens_total 30000
"""

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Run Mock Server**:
```bash
python mock_vllm_server.py
```

#### 2.3 Test Collection Endpoint

```bash
# Test metrics collection
curl -X POST http://localhost:8002/api/v1/collect/vllm \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-001",
    "endpoint": "http://localhost:8000/metrics",
    "timeout": 10
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "instance_id": "vllm-001",
  "timestamp": "2025-01-23T...",
  "metrics": {
    "timestamp": "2025-01-23T...",
    "instance_id": "vllm-001",
    "endpoint": "http://localhost:8000/metrics",
    "request_metrics": {
      "success_total": 150,
      "failure_total": 5,
      "time_to_first_token_seconds": 0.025,
      "time_per_output_token_seconds": 0.010,
      "e2e_latency_seconds": 1.5,
      "prompt_tokens": 0,
      "generation_tokens": 0
    },
    "gpu_metrics": {
      "cache_usage_perc": 75.5,
      "memory_usage_bytes": 8589934592,
      "num_requests_running": 3,
      "num_requests_waiting": 2
    },
    "throughput_metrics": {
      "prompt_tokens_total": 15000,
      "generation_tokens_total": 30000,
      "num_preemptions_total": 0,
      "requests_per_second": 0.0,
      "tokens_per_second": 0.0
    },
    "raw_metrics": [...]
  }
}
```

#### 2.4 Test GET Endpoint

```bash
curl "http://localhost:8002/api/v1/metrics/vllm/vllm-001?endpoint=http://localhost:8000/metrics"
```

---

### Step 3: Integration Testing

#### 3.1 Test with Real vLLM (If Available)

If you have a vLLM instance running:

```bash
# Assuming vLLM is running on localhost:8000
curl -X POST http://localhost:8002/api/v1/collect/vllm \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-production",
    "endpoint": "http://localhost:8000/metrics",
    "timeout": 10
  }'
```

#### 3.2 Verify Metrics Parsing

Check that all expected metrics are captured:
- Request metrics (success, failure, latency)
- GPU metrics (cache, memory, requests)
- Throughput metrics (tokens, preemptions)

---

### Step 4: Error Handling Testing

#### 4.1 Test Invalid Endpoint

```bash
curl -X POST http://localhost:8002/api/v1/collect/vllm \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-invalid",
    "endpoint": "http://invalid-host:8000/metrics",
    "timeout": 5
  }'
```

**Expected Response**:
```json
{
  "success": false,
  "instance_id": "vllm-invalid",
  "timestamp": "2025-01-23T...",
  "metrics": null,
  "error": "Connection error message..."
}
```

#### 4.2 Test Timeout

```bash
curl -X POST http://localhost:8002/api/v1/collect/vllm \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-slow",
    "endpoint": "http://slow-server:8000/metrics",
    "timeout": 1
  }'
```

---

## Validation Checklist

### Functional Validation
- [ ] Prometheus parser correctly parses metrics
- [ ] Parser handles counters, gauges, histograms
- [ ] Parser extracts labels correctly
- [ ] vLLM collector fetches metrics via HTTP
- [ ] Collector extracts request metrics
- [ ] Collector extracts GPU metrics
- [ ] Collector extracts throughput metrics
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
- [ ] Parser handles large metric sets
- [ ] No memory leaks in async operations

---

## Success Metrics

### Test Coverage
- **Target**: > 80% coverage
- **Critical Paths**: 100% coverage
  - Prometheus parsing
  - Metric extraction
  - API endpoints

### Performance Metrics
- **Collection Time**: < 5 seconds
- **Parse Time**: < 1 second for 1000 metrics
- **Memory Usage**: < 50 MB increase

---

## Troubleshooting

### Common Issues

#### Issue 1: Import Errors
**Symptom**: `ModuleNotFoundError: No module named 'src.collectors'`

**Solution**:
```bash
# Ensure __init__.py files exist
touch src/collectors/__init__.py
```

#### Issue 2: Async Context Manager Error
**Symptom**: `RuntimeError: Collector not initialized`

**Solution**:
```python
# Always use async context manager
async with VLLMCollector() as collector:
    metrics = await collector.collect(...)
```

#### Issue 3: Parsing Errors
**Symptom**: Metrics not parsed correctly

**Solution**:
- Check Prometheus text format
- Verify regex patterns
- Add debug logging

#### Issue 4: HTTP Connection Errors
**Symptom**: `httpx.ConnectError`

**Solution**:
- Verify endpoint URL
- Check network connectivity
- Increase timeout
- Check if vLLM is running

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

3. **Create Validation Report**:
- Document test results
- Document any issues
- Document performance metrics

4. **Commit Code**:
```bash
git add .
git commit -m "feat: implement PHASE2-2.2 vLLM metrics collector"
git push origin main
```

---

## Next Steps

### Immediate
1. ✅ Validate all functionality
2. ✅ Run complete test suite
3. ✅ Create completion report
4. ✅ Commit and push code

### Next Phase: PHASE2-2.3
**TGI Collector**: Implement metrics collection for Text Generation Inference
- Similar structure to vLLM collector
- TGI-specific metrics
- Integration with Performance Agent

---

## Timeline

| Task | Duration | Status |
|------|----------|--------|
| Metrics Models | 5 min | Pending |
| Prometheus Parser | 7 min | Pending |
| vLLM Collector | 5 min | Pending |
| API Endpoints | 3 min | Pending |
| Testing & Validation | 5 min | Pending |
| **Total** | **25 min** | **Pending** |

---

## Deliverables

### Code Deliverables
- ✅ Metrics models (Pydantic)
- ✅ Prometheus parser
- ✅ vLLM collector
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
4. **Parsing**: Robust parsing of Prometheus format
5. **Testing**: Mock HTTP responses for unit tests

### vLLM Metrics Reference
- **Documentation**: https://docs.vllm.ai/en/latest/serving/metrics.html
- **Endpoint**: Usually `http://host:port/metrics`
- **Format**: Prometheus text format
- **Update Frequency**: Real-time

---

**Status**: Ready for execution  
**Estimated Completion**: 20 minutes  
**Next Phase**: PHASE2-2.3 - TGI Collector
