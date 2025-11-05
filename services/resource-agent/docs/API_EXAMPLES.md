# Resource Agent API Examples

Complete examples for all Resource Agent REST API endpoints.

---

## Base URL

```
http://localhost:8003
```

---

## Health Endpoints

### 1. Root Endpoint

```bash
curl http://localhost:8003/
```

**Response:**
```json
{
  "agent": "Resource Agent",
  "version": "1.0.0",
  "status": "active",
  "agent_id": "resource-agent-001"
}
```

### 2. Basic Health Check

```bash
curl http://localhost:8003/health/
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-25T19:00:00.000000"
}
```

### 3. Detailed Health Check

```bash
curl http://localhost:8003/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-25T19:00:00.000000",
  "components": {
    "api": "healthy",
    "collectors": "healthy",
    "analysis": "healthy"
  },
  "version": "1.0.0"
}
```

---

## GPU Endpoints

### 4. GPU Info

```bash
curl http://localhost:8003/gpu/info
```

**Response (No GPU):**
```json
{
  "available": false,
  "gpu_count": 0,
  "message": "No GPU detected or pynvml not available"
}
```

**Response (With GPU):**
```json
{
  "available": true,
  "gpu_count": 2,
  "gpus": [
    {
      "index": 0,
      "name": "NVIDIA A100",
      "uuid": "GPU-12345678"
    }
  ]
}
```

### 5. All GPU Metrics

```bash
curl http://localhost:8003/gpu/metrics
```

**Response:**
```json
{
  "timestamp": "2025-10-25T19:00:00.000000",
  "instance_id": "resource-agent-001",
  "gpu_count": 2,
  "average_gpu_utilization": 80.0,
  "average_memory_utilization": 75.0,
  "total_power_draw_watts": 480.0
}
```

---

## System Endpoints

### 6. All System Metrics

```bash
curl http://localhost:8003/system/metrics
```

**Response:**
```json
{
  "timestamp": "2025-10-25T19:00:00.000000",
  "instance_id": "resource-agent-001",
  "cpu": {
    "utilization_percent": 45.5,
    "cpu_count": 16,
    "physical_cores": 8
  },
  "memory": {
    "utilization_percent": 50.0,
    "total_mb": 32768,
    "available_mb": 16384
  },
  "uptime_seconds": 432000
}
```

### 7. CPU Metrics Only

```bash
curl http://localhost:8003/system/metrics/cpu
```

### 8. Memory Metrics Only

```bash
curl http://localhost:8003/system/metrics/memory
```

---

## Analysis Endpoints

### 9. Complete Analysis

```bash
curl http://localhost:8003/analysis/
```

**Response:**
```json
{
  "timestamp": "2025-10-25T19:00:00.000000",
  "instance_id": "resource-agent-001",
  "primary_bottleneck": "memory",
  "health_score": 72.5,
  "overall_health": "degraded",
  "efficiency": {
    "overall_score": 72.5,
    "cpu_efficiency": 85.0,
    "memory_efficiency": 60.0
  },
  "recommendations": [
    {
      "title": "Optimize Memory Usage",
      "priority": "high",
      "expected_impact": "15% improvement"
    }
  ]
}
```

### 10. Health Score Only

```bash
curl http://localhost:8003/analysis/health-score
```

**Response:**
```json
{
  "health_score": 72.5,
  "overall_health": "degraded",
  "primary_bottleneck": "memory"
}
```

---

## LMCache Endpoints

### 11. LMCache Status

```bash
curl http://localhost:8003/lmcache/status
```

**Response:**
```json
{
  "timestamp": "2025-10-25T19:00:00.000000",
  "instance_id": "resource-agent-001",
  "metrics": {
    "status": "enabled",
    "hit_rate_percent": 75.0,
    "utilization_percent": 50.0,
    "memory_saved_mb": 819.2
  },
  "config": {
    "enabled": true,
    "max_size_mb": 2048.0,
    "eviction_policy": "lru"
  }
}
```

### 12. Get Cache Config

```bash
curl http://localhost:8003/lmcache/config
```

### 13. Update Cache Config

```bash
curl -X POST http://localhost:8003/lmcache/config \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "max_size_mb": 4096.0,
    "eviction_policy": "lfu"
  }'
```

### 14. Optimize Cache

```bash
curl -X POST http://localhost:8003/lmcache/optimize
```

**Response:**
```json
{
  "success": true,
  "message": "Cache optimization completed",
  "entries_evicted": 25,
  "memory_freed_mb": 128.0
}
```

### 15. Clear Cache

```bash
curl -X DELETE http://localhost:8003/lmcache/clear
```

---

## Optimization Endpoint

### 16. Run Optimization Workflow

```bash
curl -X POST http://localhost:8003/optimize/run
```

**Response:**
```json
{
  "workflow_id": "a1b2c3d4-e5f6-7890",
  "status": "completed",
  "timestamp": "2025-10-25T19:00:00.000000",
  "instance_id": "resource-agent-001",
  "health_score": 72.5,
  "primary_bottleneck": "memory",
  "llm_insights": "Memory utilization is high...",
  "actions": [
    {
      "title": "Optimize Memory Usage",
      "description": "Implement memory optimization",
      "priority": "high",
      "expected_impact": "15% improvement",
      "implementation_effort": "medium"
    }
  ],
  "execution_time_ms": 1250.5
}
```

---

## Python Client Examples

### Example 1: Get System Metrics

```python
import requests

response = requests.get("http://localhost:8003/system/metrics")
metrics = response.json()

print(f"CPU Utilization: {metrics['cpu']['utilization_percent']}%")
print(f"Memory Utilization: {metrics['memory']['utilization_percent']}%")
```

### Example 2: Run Analysis

```python
import requests

response = requests.get("http://localhost:8003/analysis/")
analysis = response.json()

print(f"Health Score: {analysis['health_score']}")
print(f"Primary Bottleneck: {analysis['primary_bottleneck']}")

for rec in analysis['recommendations']:
    print(f"- {rec['title']}: {rec['expected_impact']}")
```

### Example 3: Run Optimization Workflow

```python
import requests

response = requests.post("http://localhost:8003/optimize/run")
result = response.json()

print(f"Workflow ID: {result['workflow_id']}")
print(f"Status: {result['status']}")
print(f"Execution Time: {result['execution_time_ms']}ms")

for action in result['actions']:
    print(f"\nAction: {action['title']}")
    print(f"Priority: {action['priority']}")
    print(f"Impact: {action['expected_impact']}")
```

---

## Error Handling

### Example: Handle API Errors

```python
import requests

try:
    response = requests.get("http://localhost:8003/gpu/metrics")
    response.raise_for_status()
    metrics = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 503:
        print("GPU not available")
    else:
        print(f"API error: {e}")
except requests.exceptions.RequestException as e:
    print(f"Connection error: {e}")
```

---

## Common Use Cases

### Use Case 1: Monitor Resource Health

```bash
# Get health score
curl http://localhost:8003/analysis/health-score

# If score < 70, get detailed analysis
curl http://localhost:8003/analysis/

# Run optimization if needed
curl -X POST http://localhost:8003/optimize/run
```

### Use Case 2: Check LMCache Performance

```bash
# Get cache status
curl http://localhost:8003/lmcache/status

# If hit rate < 60%, optimize
curl -X POST http://localhost:8003/lmcache/optimize
```

### Use Case 3: Continuous Monitoring

```bash
# Poll every 60 seconds
while true; do
  curl http://localhost:8003/analysis/health-score
  sleep 60
done
```

---

## API Documentation

Full OpenAPI documentation available at:
- **Swagger UI**: http://localhost:8003/docs
- **ReDoc**: http://localhost:8003/redoc

---

**Resource Agent API v1.0.0** 🚀
