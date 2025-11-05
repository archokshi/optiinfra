# PHASE3-3.3 PART2: CPU/Memory Collector - Execution and Validation

**Phase**: PHASE3-3.3  
**Agent**: Resource Agent  
**Objective**: Execute CPU/Memory collector implementation and validate functionality  
**Estimated Time**: 20 minutes  
**Prerequisites**: PART1 completed, PHASE3-3.1, PHASE3-3.2 completed

---

## Execution Steps

### Step 1: Create System Metrics Models (3 minutes)

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra\services\resource-agent
```

1. **Create src/models/system_metrics.py**
   - Copy the complete model definitions from PART1

**Verification:**
```bash
python -c "from src.models.system_metrics import SystemMetricsCollection; print('Models OK')"
```

**Expected Output:**
```
Models OK
```

---

### Step 2: Create System Collector (5 minutes)

1. **Create src/collectors/system_collector.py**
   - Copy the complete collector implementation from PART1

**Verification:**
```bash
python -c "from src.collectors.system_collector import SystemCollector; print('Collector OK')"
```

**Expected Output:**
```
Collector OK
```

---

### Step 3: Create API Endpoint (3 minutes)

1. **Create src/api/system.py**
   - Copy the API endpoint implementation from PART1

2. **Update src/main.py**
   - Add system router import and include

**Verification:**
```bash
python -c "from src.api.system import router; print('API OK')"
```

**Expected Output:**
```
API OK
```

---

### Step 4: Create Tests (4 minutes)

1. **Create tests/test_system_collector.py**
2. **Create tests/test_system_api.py**

**Verification:**
```bash
python -m pytest tests/test_system_collector.py -v
python -m pytest tests/test_system_api.py -v
```

**Expected Output:**
```
tests/test_system_collector.py::test_system_collector_initialization PASSED
tests/test_system_collector.py::test_collect_cpu_metrics PASSED
tests/test_system_collector.py::test_collect_memory_metrics PASSED
tests/test_system_collector.py::test_collect_disk_metrics PASSED
tests/test_system_collector.py::test_collect_network_metrics PASSED
tests/test_system_collector.py::test_collect_all_metrics PASSED

tests/test_system_api.py::test_get_system_metrics PASSED
tests/test_system_api.py::test_get_cpu_metrics PASSED
tests/test_system_api.py::test_get_memory_metrics PASSED
tests/test_system_api.py::test_get_disk_metrics PASSED
tests/test_system_api.py::test_get_network_metrics PASSED
```

---

### Step 5: Run All Tests (2 minutes)

```bash
pytest tests/ -v --cov=src
```

**Expected Output:**
```
tests/test_gpu_api.py::test_get_gpu_info PASSED
tests/test_gpu_collector.py::test_gpu_collector_without_pynvml PASSED
tests/test_health.py::test_health_check PASSED
tests/test_health.py::test_detailed_health_check PASSED
tests/test_health.py::test_readiness_check PASSED
tests/test_health.py::test_liveness_check PASSED
tests/test_health.py::test_root_endpoint PASSED
tests/test_system_api.py::test_get_system_metrics PASSED
tests/test_system_api.py::test_get_cpu_metrics PASSED
tests/test_system_api.py::test_get_memory_metrics PASSED
tests/test_system_api.py::test_get_disk_metrics PASSED
tests/test_system_api.py::test_get_network_metrics PASSED
tests/test_system_collector.py::test_system_collector_initialization PASSED
tests/test_system_collector.py::test_collect_cpu_metrics PASSED
tests/test_system_collector.py::test_collect_memory_metrics PASSED
tests/test_system_collector.py::test_collect_disk_metrics PASSED
tests/test_system_collector.py::test_collect_network_metrics PASSED
tests/test_system_collector.py::test_collect_all_metrics PASSED

========== 18+ passed ==========
Coverage: 60%+
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
2025-10-24 23:00:00 - resource_agent - INFO - Starting Resource Agent: resource-agent-001
2025-10-24 23:00:00 - resource_agent - INFO - Environment: development
2025-10-24 23:00:00 - resource_agent - INFO - Port: 8003
INFO:     Application startup complete.
```

---

## Validation Steps

### Step 7: Test System Metrics Endpoint (2 minutes)

```bash
curl http://localhost:8003/system/metrics
```

**Expected Response:**
```json
{
  "timestamp": "2025-10-24T23:00:00.000000",
  "instance_id": "resource-agent-001",
  "cpu": {
    "utilization_percent": 25.5,
    "per_core_utilization": [30.0, 25.0, 22.0, 24.0],
    "logical_cores": 4,
    "physical_cores": 2,
    "frequency": {
      "current_mhz": 2400.0,
      "min_mhz": 800.0,
      "max_mhz": 3600.0
    },
    "load_average_1m": 1.5,
    "load_average_5m": 1.2,
    "load_average_15m": 1.0,
    "cpu_times": {
      "user": 1234.5,
      "system": 567.8,
      "idle": 8901.2,
      "iowait": 45.3
    },
    "context_switches": 123456
  },
  "memory": {
    "total_mb": 16384.0,
    "available_mb": 8192.0,
    "used_mb": 8192.0,
    "free_mb": 4096.0,
    "utilization_percent": 50.0,
    "swap_total_mb": 4096.0,
    "swap_used_mb": 512.0,
    "swap_free_mb": 3584.0,
    "swap_utilization_percent": 12.5,
    "cached_mb": 2048.0,
    "buffers_mb": 512.0
  },
  "disk": {
    "partitions": [
      {
        "device": "/dev/sda1",
        "mountpoint": "/",
        "fstype": "ext4",
        "total_mb": 102400.0,
        "used_mb": 51200.0,
        "free_mb": 51200.0,
        "utilization_percent": 50.0
      }
    ],
    "io_counters": {
      "read_bytes": 1073741824,
      "write_bytes": 536870912,
      "read_count": 10000,
      "write_count": 5000
    }
  },
  "network": {
    "io_counters": {
      "bytes_sent": 1073741824,
      "bytes_recv": 2147483648,
      "packets_sent": 1000000,
      "packets_recv": 2000000,
      "errin": 0,
      "errout": 0,
      "dropin": 0,
      "dropout": 0
    },
    "connections_count": 50
  },
  "boot_time": "2025-10-20T10:00:00",
  "uptime_seconds": 345600.0
}
```

---

### Step 8: Test CPU Metrics Endpoint (1 minute)

```bash
curl http://localhost:8003/system/metrics/cpu
```

**Expected Response:**
```json
{
  "utilization_percent": 25.5,
  "per_core_utilization": [30.0, 25.0, 22.0, 24.0],
  "logical_cores": 4,
  "physical_cores": 2,
  "frequency": {
    "current_mhz": 2400.0,
    "min_mhz": 800.0,
    "max_mhz": 3600.0
  },
  "load_average_1m": 1.5,
  "load_average_5m": 1.2,
  "load_average_15m": 1.0,
  "cpu_times": {
    "user": 1234.5,
    "system": 567.8,
    "idle": 8901.2,
    "iowait": 45.3
  },
  "context_switches": 123456
}
```

---

### Step 9: Test Memory Metrics Endpoint (1 minute)

```bash
curl http://localhost:8003/system/metrics/memory
```

**Expected Response:**
```json
{
  "total_mb": 16384.0,
  "available_mb": 8192.0,
  "used_mb": 8192.0,
  "free_mb": 4096.0,
  "utilization_percent": 50.0,
  "swap_total_mb": 4096.0,
  "swap_used_mb": 512.0,
  "swap_free_mb": 3584.0,
  "swap_utilization_percent": 12.5,
  "cached_mb": 2048.0,
  "buffers_mb": 512.0
}
```

---

### Step 10: Test Disk Metrics Endpoint (1 minute)

```bash
curl http://localhost:8003/system/metrics/disk
```

**Expected Response:**
```json
{
  "partitions": [
    {
      "device": "C:\\",
      "mountpoint": "C:\\",
      "fstype": "NTFS",
      "total_mb": 512000.0,
      "used_mb": 256000.0,
      "free_mb": 256000.0,
      "utilization_percent": 50.0
    }
  ],
  "io_counters": {
    "read_bytes": 1073741824,
    "write_bytes": 536870912,
    "read_count": 10000,
    "write_count": 5000
  }
}
```

---

### Step 11: Test Network Metrics Endpoint (1 minute)

```bash
curl http://localhost:8003/system/metrics/network
```

**Expected Response:**
```json
{
  "io_counters": {
    "bytes_sent": 1073741824,
    "bytes_recv": 2147483648,
    "packets_sent": 1000000,
    "packets_recv": 2000000,
    "errin": 0,
    "errout": 0,
    "dropin": 0,
    "dropout": 0
  },
  "connections_count": 50
}
```

---

### Step 12: Test API Documentation (1 minute)

Open browser and navigate to:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

**Verify:**
- [ ] System endpoints visible in documentation
- [ ] Request/response schemas displayed correctly
- [ ] "Try it out" functionality works

---

## Validation Checklist

### Functionality Tests

- [ ] **System Metrics**: `/system/metrics` returns all metrics
- [ ] **CPU Metrics**: `/system/metrics/cpu` returns CPU data
- [ ] **Memory Metrics**: `/system/metrics/memory` returns memory data
- [ ] **Disk Metrics**: `/system/metrics/disk` returns disk data
- [ ] **Network Metrics**: `/system/metrics/network` returns network data
- [ ] **Accurate Data**: Metrics reflect actual system state

### Code Quality Tests

- [ ] **All Tests Pass**: 18+ tests passing
- [ ] **Code Coverage**: Coverage > 60%
- [ ] **No Import Errors**: All modules import successfully
- [ ] **Type Hints**: All functions have type hints

### Integration Tests

- [ ] **Health Check**: Still works after adding system collector
- [ ] **GPU Endpoints**: Still functional
- [ ] **API Docs**: System endpoints in Swagger UI

---

## Troubleshooting

### Issue: Permission Denied for Network Connections

**Problem**: `PermissionError` when collecting network connections

**Solution**:
- This is expected on some systems
- Collector gracefully handles this (connections_count will be None)
- Other network metrics still collected

---

### Issue: Load Average Not Available (Windows)

**Problem**: `load_average_1m`, `load_average_5m`, `load_average_15m` are null

**Solution**:
- Load average is Unix/Linux only
- Windows doesn't have this metric
- This is expected behavior

---

### Issue: Disk Metrics Missing Some Partitions

**Problem**: Some disk partitions not showing up

**Solution**:
- Permission issues on some mount points
- Collector skips inaccessible partitions
- This is expected behavior

---

### Issue: CPU Utilization Shows 0%

**Problem**: CPU utilization always shows 0%

**Solution**:
- First call to `cpu_percent()` returns 0
- Collector uses `interval=1` to get accurate reading
- Subsequent calls will show correct values

---

## Performance Metrics

### Expected Performance

- **System Metrics Collection**: < 2 seconds (includes 1s CPU interval)
- **CPU Metrics Only**: < 1.5 seconds
- **Memory Metrics Only**: < 50ms
- **Disk Metrics Only**: < 200ms
- **Network Metrics Only**: < 100ms

### Benchmark Commands

```bash
# Response time test
time curl http://localhost:8003/system/metrics/memory

# Load test (if apache-bench installed)
ab -n 100 -c 5 http://localhost:8003/system/metrics/memory
```

**Expected ab Output:**
```
Requests per second:    100+ [#/sec]
Time per request:       50ms [mean]
```

---

## Testing on Different Platforms

### Windows

**Expected Behavior:**
- ✅ CPU metrics collected
- ✅ Memory metrics collected
- ✅ Disk metrics collected (NTFS partitions)
- ❌ Load average not available (null)
- ⚠️ Some network metrics may require admin

### Linux

**Expected Behavior:**
- ✅ CPU metrics collected
- ✅ Memory metrics collected (with cached/buffers)
- ✅ Disk metrics collected (ext4, xfs, etc.)
- ✅ Load average available
- ✅ Full network metrics

### macOS

**Expected Behavior:**
- ✅ CPU metrics collected
- ✅ Memory metrics collected
- ✅ Disk metrics collected (APFS, HFS+)
- ✅ Load average available
- ✅ Network metrics collected

---

## Success Criteria

### Must Have ✅

- [x] System collector implemented
- [x] API endpoints functional (5 endpoints)
- [x] Tests pass (18+ tests)
- [x] Cross-platform compatibility
- [x] Documentation complete

### Nice to Have 🎯

- [ ] Per-process metrics
- [ ] Historical metrics tracking
- [ ] Metrics caching
- [ ] Performance benchmarks documented

---

## Next Phase Preview

**PHASE3-3.4: Analysis Engine**

What we'll build:
- Utilization analysis
- Bottleneck detection
- Resource optimization recommendations
- Trend analysis
- Alerting thresholds

**Estimated Time**: 30+20m (50 minutes)

---

## Completion Summary

After completing this phase, you will have:

1. ✅ **Comprehensive System Metrics**
   - CPU utilization and per-core metrics
   - Memory usage with swap
   - Disk usage and I/O
   - Network I/O

2. ✅ **API Endpoints**
   - `/system/metrics` - All metrics
   - `/system/metrics/cpu` - CPU only
   - `/system/metrics/memory` - Memory only
   - `/system/metrics/disk` - Disk only
   - `/system/metrics/network` - Network only

3. ✅ **Production Ready**
   - Cross-platform support
   - Error handling
   - Performance optimized

4. ✅ **Documentation**
   - API documentation
   - Troubleshooting guide
   - Platform-specific notes

---

**System metrics collector is ready! Let's move to analysis engine.** 🚀
