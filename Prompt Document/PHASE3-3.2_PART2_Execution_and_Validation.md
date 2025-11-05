# PHASE3-3.2 PART2: GPU Collector - Execution and Validation

**Phase**: PHASE3-3.2  
**Agent**: Resource Agent  
**Objective**: Execute GPU collector implementation and validate functionality  
**Estimated Time**: 20 minutes  
**Prerequisites**: PART1 completed, PHASE3-3.1 completed

---

## Execution Steps

### Step 1: Create GPU Metrics Models (3 minutes)

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\resource-agent
```

1. **Create src/models/gpu_metrics.py**
   - Copy the complete model definitions from PART1

**Verification:**
```bash
python -c "from src.models.gpu_metrics import GPUMetricsCollection; print('Models OK')"
```

**Expected Output:**
```
Models OK
```

---

### Step 2: Create GPU Collector (5 minutes)

1. **Create src/collectors/__init__.py**
2. **Create src/collectors/gpu_collector.py**
   - Copy the complete collector implementation from PART1

**Verification:**
```bash
python -c "from src.collectors.gpu_collector import GPUCollector; print('Collector OK')"
```

**Expected Output:**
```
Collector OK
```

---

### Step 3: Create API Endpoint (3 minutes)

1. **Create src/api/gpu.py**
   - Copy the API endpoint implementation from PART1

2. **Update src/main.py**
   - Add GPU router import and include

**Verification:**
```bash
python -c "from src.api.gpu import router; print('API OK')"
```

**Expected Output:**
```
API OK
```

---

### Step 4: Create Tests (4 minutes)

1. **Create tests/test_gpu_collector.py**
2. **Create tests/test_gpu_api.py**

**Verification:**
```bash
python -m pytest tests/test_gpu_collector.py -v
python -m pytest tests/test_gpu_api.py -v
```

**Expected Output:**
```
tests/test_gpu_collector.py::test_gpu_collector_initialization PASSED
tests/test_gpu_collector.py::test_collect_single_gpu_metrics PASSED
tests/test_gpu_collector.py::test_collect_all_gpu_metrics PASSED
tests/test_gpu_collector.py::test_gpu_collector_without_pynvml PASSED

tests/test_gpu_api.py::test_get_gpu_info PASSED
tests/test_gpu_api.py::test_get_gpu_metrics SKIPPED (requires GPU)
tests/test_gpu_api.py::test_get_single_gpu_metrics SKIPPED (requires GPU)
```

---

### Step 5: Run All Tests (2 minutes)

```bash
pytest tests/ -v --cov=src
```

**Expected Output:**
```
tests/test_gpu_api.py::test_get_gpu_info PASSED
tests/test_gpu_collector.py::test_gpu_collector_initialization PASSED
tests/test_gpu_collector.py::test_collect_single_gpu_metrics PASSED
tests/test_gpu_collector.py::test_collect_all_gpu_metrics PASSED
tests/test_gpu_collector.py::test_gpu_collector_without_pynvml PASSED
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_detailed_health_check PASSED
tests/test_health.py::test_readiness_check PASSED
tests/test_health.py::test_liveness_check PASSED
tests/test_health.py::test_root_endpoint PASSED

========== 10 passed, 2 skipped ==========
Coverage: 65%+
```

---

### Step 6: Start Application (2 minutes)

```bash
python -m uvicorn src.main:app --reload --port 8003
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['C:\\...\\resource-agent']
INFO:     Uvicorn running on http://127.0.0.1:8003 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using StatReload
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
2025-10-24 22:00:00 - resource_agent - INFO - Starting Resource Agent: resource-agent-001
2025-10-24 22:00:00 - resource_agent - INFO - Environment: development
2025-10-24 22:00:00 - resource_agent - INFO - Port: 8003
INFO:     Application startup complete.
```

---

## Validation Steps

### Step 7: Test GPU Info Endpoint (1 minute)

```bash
curl http://localhost:8003/gpu/info
```

**Expected Response (with GPU):**
```json
{
  "available": true,
  "gpu_count": 1,
  "pynvml_installed": true
}
```

**Expected Response (without GPU):**
```json
{
  "available": false,
  "gpu_count": 0,
  "pynvml_installed": false
}
```

---

### Step 8: Test GPU Metrics Endpoint (2 minutes)

**If GPU Available:**
```bash
curl http://localhost:8003/gpu/metrics
```

**Expected Response:**
```json
{
  "timestamp": "2025-10-24T22:00:00.000000",
  "instance_id": "resource-agent-001",
  "gpu_count": 1,
  "gpus": [
    {
      "gpu_id": 0,
      "gpu_name": "NVIDIA GeForce RTX 3090",
      "gpu_uuid": "GPU-12345678-1234-1234-1234-123456789012",
      "driver_version": "525.60.13",
      "utilization": {
        "gpu_percent": 45.0,
        "memory_percent": 30.0,
        "encoder_percent": null,
        "decoder_percent": null
      },
      "memory": {
        "total_mb": 24576.0,
        "used_mb": 7372.8,
        "free_mb": 17203.2,
        "utilization_percent": 30.0
      },
      "temperature": {
        "current_celsius": 55.0,
        "slowdown_threshold_celsius": 83.0,
        "shutdown_threshold_celsius": 90.0
      },
      "power": {
        "power_draw_watts": 250.5,
        "power_limit_watts": 350.0,
        "power_usage_percent": 71.57
      },
      "clocks": {
        "graphics_clock_mhz": 1710.0,
        "sm_clock_mhz": 1710.0,
        "memory_clock_mhz": 9751.0
      },
      "processes": [
        {
          "pid": 12345,
          "process_name": "python",
          "used_memory_mb": 2048.0
        }
      ],
      "performance_state": "P0",
      "fan_speed_percent": 45.0
    }
  ],
  "total_memory_used_mb": 7372.8,
  "total_memory_total_mb": 24576.0,
  "average_gpu_utilization": 45.0,
  "average_memory_utilization": 30.0,
  "average_temperature": 55.0,
  "total_power_draw_watts": 250.5
}
```

**If GPU Not Available:**
```bash
curl http://localhost:8003/gpu/metrics
```

**Expected Response:**
```json
{
  "detail": "GPU metrics collection not available (no NVIDIA GPUs or pynvml not installed)"
}
```
Status Code: 503

---

### Step 9: Test Single GPU Endpoint (1 minute)

**If GPU Available:**
```bash
curl http://localhost:8003/gpu/metrics/0
```

**Expected Response:**
```json
{
  "gpu_id": 0,
  "gpu_name": "NVIDIA GeForce RTX 3090",
  "gpu_uuid": "GPU-12345678-1234-1234-1234-123456789012",
  "driver_version": "525.60.13",
  "utilization": {
    "gpu_percent": 45.0,
    "memory_percent": 30.0
  },
  "memory": {
    "total_mb": 24576.0,
    "used_mb": 7372.8,
    "free_mb": 17203.2,
    "utilization_percent": 30.0
  },
  "temperature": {
    "current_celsius": 55.0
  },
  "power": {
    "power_draw_watts": 250.5,
    "power_limit_watts": 350.0,
    "power_usage_percent": 71.57
  },
  "clocks": {
    "graphics_clock_mhz": 1710.0,
    "sm_clock_mhz": 1710.0,
    "memory_clock_mhz": 9751.0
  },
  "processes": [],
  "performance_state": "P0",
  "fan_speed_percent": 45.0
}
```

---

### Step 10: Test API Documentation (1 minute)

Open browser and navigate to:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

**Verify:**
- [ ] GPU endpoints visible in documentation
- [ ] Request/response schemas displayed correctly
- [ ] "Try it out" functionality works

---

## Validation Checklist

### Functionality Tests

- [ ] **GPU Info**: `/gpu/info` returns GPU availability
- [ ] **GPU Metrics**: `/gpu/metrics` returns metrics (or 503 if no GPU)
- [ ] **Single GPU**: `/gpu/metrics/{id}` returns single GPU metrics
- [ ] **Error Handling**: Invalid GPU ID returns 404
- [ ] **Graceful Degradation**: Works without GPU hardware

### Code Quality Tests

- [ ] **All Tests Pass**: 10+ tests passing
- [ ] **Code Coverage**: Coverage > 65%
- [ ] **No Import Errors**: All modules import successfully
- [ ] **Type Hints**: All functions have type hints

### Integration Tests

- [ ] **Health Check**: Still works after adding GPU collector
- [ ] **API Docs**: GPU endpoints in Swagger UI
- [ ] **Multiple GPUs**: Works with multi-GPU systems (if available)

---

## Troubleshooting

### Issue: pynvml Not Installed

**Problem**: `ModuleNotFoundError: No module named 'pynvml'`

**Solution**:
```bash
pip install nvidia-ml-py
```

---

### Issue: NVIDIA Driver Not Found

**Problem**: `Failed to initialize pynvml: NVML Shared Library Not Found`

**Solution**:
- Install NVIDIA drivers
- Or accept graceful degradation (GPU metrics will be unavailable)

---

### Issue: Permission Denied

**Problem**: `NVML: Insufficient Permissions`

**Solution**:
- Run with appropriate permissions
- Check NVIDIA driver installation

---

### Issue: GPU Metrics Return 503

**Problem**: GPU metrics endpoint returns 503 Service Unavailable

**Solution**:
- This is expected if no NVIDIA GPU is present
- Check `/gpu/info` to verify GPU availability
- Collector will work on systems with NVIDIA GPUs

---

## Performance Metrics

### Expected Performance

- **GPU Metrics Collection**: < 100ms per GPU
- **API Response Time**: < 150ms
- **Memory Overhead**: < 50MB
- **CPU Usage**: < 2% (idle)

### Benchmark Commands

```bash
# Response time test
time curl http://localhost:8003/gpu/metrics

# Load test (if apache-bench installed)
ab -n 100 -c 5 http://localhost:8003/gpu/info
```

**Expected ab Output:**
```
Requests per second:    200+ [#/sec]
Time per request:       25ms [mean]
```

---

## Testing on Different Environments

### Environment 1: System with NVIDIA GPU

**Expected Behavior:**
- ✅ GPU collector initializes
- ✅ Metrics collected successfully
- ✅ All GPU endpoints return 200 OK
- ✅ Real GPU data in responses

### Environment 2: System without NVIDIA GPU

**Expected Behavior:**
- ✅ GPU collector initializes with warning
- ✅ `/gpu/info` returns `available: false`
- ✅ `/gpu/metrics` returns 503
- ✅ Application still functions normally
- ✅ Other endpoints unaffected

### Environment 3: Docker Container

**Expected Behavior:**
- ✅ Requires `--gpus all` flag
- ✅ NVIDIA Container Toolkit installed
- ✅ GPU metrics accessible in container

---

## Success Criteria

### Must Have ✅

- [x] GPU collector implemented
- [x] API endpoints functional
- [x] Tests pass (10+ tests)
- [x] Graceful degradation without GPU
- [x] Documentation complete

### Nice to Have 🎯

- [ ] Multi-GPU support verified
- [ ] Process-level GPU usage tracked
- [ ] Performance benchmarks documented
- [ ] Docker GPU support tested

---

## Next Phase Preview

**PHASE3-3.3: CPU/Memory Collector**

What we'll build:
- psutil integration
- CPU utilization monitoring
- Memory usage tracking
- Disk I/O metrics
- Network metrics

**Estimated Time**: 25+20m (45 minutes)

---

## Completion Summary

After completing this phase, you will have:

1. ✅ **GPU Metrics Collection**
   - Real-time GPU monitoring
   - Multi-GPU support
   - Process-level tracking

2. ✅ **API Endpoints**
   - `/gpu/info` - GPU availability
   - `/gpu/metrics` - All GPU metrics
   - `/gpu/metrics/{id}` - Single GPU metrics

3. ✅ **Production Ready**
   - Graceful degradation
   - Error handling
   - Test coverage

4. ✅ **Documentation**
   - API documentation
   - Troubleshooting guide
   - Performance metrics

---

**GPU collector is ready! Let's move to CPU/Memory metrics collection.** 🚀
