# Performance Agent User Guide

## Quick Start

### 1. Start the Agent

```bash
uvicorn src.main:app --reload --port 8002
```

### 2. Verify It's Running

```bash
curl http://localhost:8002/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 3. View API Documentation

Open in your browser:
- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

---

## Common Use Cases

### Use Case 1: Monitor vLLM Instance

Collect metrics from a vLLM instance and check its performance.

**Python Example**:
```python
import requests

# Collect metrics
response = requests.post(
    "http://localhost:8002/api/v1/metrics/collect",
    json={
        "instance_id": "vllm-1",
        "instance_type": "vllm",
        "metrics_url": "http://vllm-instance:8000/metrics"
    }
)

metrics = response.json()

# Print key metrics
print(f"Success rate: {metrics['request_metrics']['success_total']}")
print(f"Throughput: {metrics['throughput_metrics']['tokens_per_second']} tokens/sec")
print(f"Memory usage: {metrics['gpu_metrics']['cache_usage_perc']}%")
```

**cURL Example**:
```bash
curl -X POST http://localhost:8002/api/v1/metrics/collect \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-1",
    "instance_type": "vllm",
    "metrics_url": "http://vllm-instance:8000/metrics"
  }'
```

---

### Use Case 2: Detect Bottlenecks

Analyze collected metrics to identify performance issues.

**Python Example**:
```python
import requests

# First, collect metrics
metrics_response = requests.post(
    "http://localhost:8002/api/v1/metrics/collect",
    json={
        "instance_id": "vllm-1",
        "instance_type": "vllm",
        "metrics_url": "http://vllm-instance:8000/metrics"
    }
)
metrics = metrics_response.json()

# Detect bottlenecks
bottlenecks_response = requests.post(
    "http://localhost:8002/api/v1/analysis/detect-bottlenecks",
    json={
        "instance_id": "vllm-1",
        "metrics": metrics
    }
)

bottlenecks = bottlenecks_response.json()['bottlenecks']

# Print bottlenecks
for b in bottlenecks:
    print(f"⚠️  {b['type']} ({b['severity']})")
    print(f"   {b['description']}")
    print(f"   Recommendation: {b['recommendation']}\n")
```

**Expected Output**:
```
⚠️  MEMORY_PRESSURE (HIGH)
   GPU memory usage at 90%, approaching capacity
   Recommendation: Enable quantization or reduce batch size

⚠️  HIGH_LATENCY (MEDIUM)
   Time to first token exceeds threshold
   Recommendation: Optimize KV cache or enable speculative decoding
```

---

### Use Case 3: Get Optimization Recommendations

Get specific optimization recommendations based on detected bottlenecks.

**Python Example**:
```python
import requests

# Get recommendations
response = requests.post(
    "http://localhost:8002/api/v1/optimization/recommend",
    json={
        "instance_id": "vllm-1",
        "instance_type": "vllm",
        "bottlenecks": bottlenecks,  # From previous step
        "current_config": {
            "max_batch_size": 32,
            "quantization": None
        }
    }
)

optimizations = response.json()['optimizations']

# Print recommendations
for opt in optimizations:
    print(f"🔧 {opt['type']} (Priority: {opt['priority']})")
    print(f"   {opt['description']}")
    print(f"   Estimated improvement: {opt['estimated_improvement']}")
    if opt.get('risks'):
        print(f"   Risks: {', '.join(opt['risks'])}\n")
```

**Expected Output**:
```
🔧 QUANTIZATION (Priority: HIGH)
   Enable INT4 quantization to reduce memory usage by 50%
   Estimated improvement: {'memory_reduction': 0.5, 'latency_impact': 0.1}
   Risks: Slight accuracy degradation possible, Requires model reload

🔧 KV_CACHE (Priority: MEDIUM)
   Optimize KV cache block size
   Estimated improvement: {'memory_reduction': 0.15}
```

---

### Use Case 4: Run Optimization Workflow

Start a complete optimization workflow with approval gates.

**Python Example**:
```python
import requests
import time

# Start workflow
workflow_response = requests.post(
    "http://localhost:8002/api/v1/workflows",
    json={
        "instance_id": "vllm-1",
        "instance_type": "vllm",
        "workflow_type": "optimization"
    }
)

workflow = workflow_response.json()
workflow_id = workflow['workflow_id']

print(f"✅ Workflow created: {workflow_id}")
print(f"   Status: {workflow['status']}")
print(f"   Optimizations: {len(workflow['optimizations'])}")

# Approve workflow
if workflow['requires_approval']:
    approve_response = requests.post(
        f"http://localhost:8002/api/v1/workflows/{workflow_id}/approve"
    )
    print(f"✅ Workflow approved")

# Monitor workflow progress
while True:
    status_response = requests.get(
        f"http://localhost:8002/api/v1/workflows/{workflow_id}"
    )
    workflow_status = status_response.json()
    
    print(f"📊 Status: {workflow_status['status']}")
    print(f"   Stage: {workflow_status.get('current_stage', 'N/A')}")
    print(f"   Progress: {workflow_status.get('progress', 0)*100:.0f}%")
    
    if workflow_status['status'] in ['COMPLETED', 'FAILED', 'REJECTED']:
        break
    
    time.sleep(5)

print(f"🎉 Workflow {workflow_status['status']}")
```

---

### Use Case 5: Monitor Multiple Instances

Monitor multiple LLM instances simultaneously.

**Python Example**:
```python
import requests
import asyncio
import aiohttp

instances = [
    {"id": "vllm-1", "type": "vllm", "url": "http://vllm-1:8000/metrics"},
    {"id": "tgi-1", "type": "tgi", "url": "http://tgi-1:8080/metrics"},
    {"id": "sglang-1", "type": "sglang", "url": "http://sglang-1:8000/metrics"}
]

async def collect_metrics(session, instance):
    async with session.post(
        "http://localhost:8002/api/v1/metrics/collect",
        json={
            "instance_id": instance["id"],
            "instance_type": instance["type"],
            "metrics_url": instance["url"]
        }
    ) as response:
        return await response.json()

async def monitor_all():
    async with aiohttp.ClientSession() as session:
        tasks = [collect_metrics(session, inst) for inst in instances]
        results = await asyncio.gather(*tasks)
        
        for inst, metrics in zip(instances, results):
            print(f"\n📊 {inst['id']} ({inst['type']})")
            print(f"   Throughput: {metrics['throughput_metrics']['tokens_per_second']:.1f} tok/s")
            print(f"   Memory: {metrics['gpu_metrics']['cache_usage_perc']:.1f}%")
            print(f"   Success rate: {metrics['request_metrics']['success_total']}")

# Run monitoring
asyncio.run(monitor_all())
```

---

## Best Practices

### 1. Regular Monitoring

Monitor instances every 30-60 seconds:

```python
import time

while True:
    # Collect metrics
    metrics = collect_metrics("vllm-1")
    
    # Check for issues
    if metrics['gpu_metrics']['cache_usage_perc'] > 90:
        print("⚠️  High memory usage detected!")
    
    time.sleep(30)
```

### 2. Gradual Rollout

Always use canary deployments for optimizations:

```python
# Start workflow with canary stage
workflow = start_workflow(
    instance_id="vllm-1",
    auto_approve=False  # Require manual approval
)

# Monitor canary performance
# Only approve full rollout if canary succeeds
```

### 3. Validation After Optimization

Always validate performance after applying optimizations:

```python
# Collect baseline metrics
baseline = collect_metrics("vllm-1")

# Apply optimization
workflow = start_workflow("vllm-1")
wait_for_completion(workflow['workflow_id'])

# Collect new metrics
optimized = collect_metrics("vllm-1")

# Compare
improvement = (
    optimized['throughput_metrics']['tokens_per_second'] /
    baseline['throughput_metrics']['tokens_per_second']
)
print(f"Throughput improvement: {improvement*100:.1f}%")
```

### 4. Keep Rollback Plan

Always keep previous configurations for rollback:

```python
# Save current config before optimization
current_config = get_instance_config("vllm-1")
save_config_backup(current_config)

# Apply optimization
apply_optimization(...)

# If issues occur, rollback
if has_issues():
    restore_config(current_config)
```

### 5. Monitor SLOs

Set up SLO monitoring:

```python
SLO_THRESHOLDS = {
    "p50_latency": 0.1,      # 100ms
    "p99_latency": 0.5,      # 500ms
    "throughput": 100.0,     # 100 tok/s
    "error_rate": 0.01       # 1%
}

def check_slos(metrics):
    violations = []
    
    if metrics['request_metrics']['time_to_first_token_seconds'] > SLO_THRESHOLDS['p50_latency']:
        violations.append("Latency SLO violated")
    
    if metrics['throughput_metrics']['tokens_per_second'] < SLO_THRESHOLDS['throughput']:
        violations.append("Throughput SLO violated")
    
    return violations
```

---

## Troubleshooting

### Problem: No Metrics Collected

**Symptoms**:
- Empty metrics response
- Connection errors

**Solutions**:
1. Verify instance is running:
   ```bash
   curl http://vllm-instance:8000/metrics
   ```

2. Check network connectivity:
   ```bash
   ping vllm-instance
   ```

3. Verify metrics endpoint format:
   ```bash
   curl http://vllm-instance:8000/metrics | head -20
   ```

---

### Problem: Bottlenecks Not Detected

**Symptoms**:
- Empty bottlenecks array
- All metrics appear normal

**Solutions**:
1. Check if metrics are actually problematic:
   ```python
   print(f"Memory: {metrics['gpu_metrics']['cache_usage_perc']}%")
   print(f"Latency: {metrics['request_metrics']['time_to_first_token_seconds']}s")
   ```

2. Adjust thresholds if needed:
   ```python
   # Lower thresholds for more sensitive detection
   THRESHOLDS = {
       "memory_usage": 0.7,  # 70% instead of 80%
       "ttft": 0.08          # 80ms instead of 100ms
   }
   ```

---

### Problem: Workflow Stuck

**Symptoms**:
- Workflow status not changing
- Stuck in PENDING_APPROVAL

**Solutions**:
1. Check workflow status:
   ```bash
   curl http://localhost:8002/api/v1/workflows/{workflow_id}
   ```

2. Approve if needed:
   ```bash
   curl -X POST http://localhost:8002/api/v1/workflows/{workflow_id}/approve
   ```

3. Check orchestrator logs:
   ```bash
   kubectl logs -n optiinfra orchestrator-xxx
   ```

---

### Problem: High Response Times

**Symptoms**:
- API calls taking > 1 second
- Timeouts

**Solutions**:
1. Check agent load:
   ```bash
   curl http://localhost:8002/metrics | grep duration
   ```

2. Increase workers:
   ```bash
   uvicorn src.main:app --workers 4
   ```

3. Check instance metrics endpoint:
   ```bash
   time curl http://vllm-instance:8000/metrics
   ```

---

## Advanced Usage

### Custom Collectors

Create custom collectors for new instance types:

```python
from src.collectors.base import BaseCollector

class CustomCollector(BaseCollector):
    async def collect(self, instance_id, metrics_url):
        # Implement custom collection logic
        pass
```

### Custom Optimizers

Create custom optimizers:

```python
from src.optimization.base import BaseOptimizer

class CustomOptimizer(BaseOptimizer):
    def generate_optimizations(self, bottlenecks, instance_type, config):
        # Implement custom optimization logic
        pass
```

### Webhooks

Set up webhooks for workflow events:

```python
# Configure webhook URL
WEBHOOK_URL = "https://your-service.com/webhook"

# Workflow will POST to webhook on status changes
```

---

## API Client Library

### Python Client

```python
class PerformanceAgentClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def collect_metrics(self, instance_id, instance_type, metrics_url):
        response = self.session.post(
            f"{self.base_url}/api/v1/metrics/collect",
            json={
                "instance_id": instance_id,
                "instance_type": instance_type,
                "metrics_url": metrics_url
            }
        )
        response.raise_for_status()
        return response.json()
    
    def detect_bottlenecks(self, instance_id, metrics):
        response = self.session.post(
            f"{self.base_url}/api/v1/analysis/detect-bottlenecks",
            json={"instance_id": instance_id, "metrics": metrics}
        )
        response.raise_for_status()
        return response.json()
    
    def start_workflow(self, instance_id, instance_type):
        response = self.session.post(
            f"{self.base_url}/api/v1/workflows",
            json={
                "instance_id": instance_id,
                "instance_type": instance_type,
                "workflow_type": "optimization"
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
client = PerformanceAgentClient()
metrics = client.collect_metrics("vllm-1", "vllm", "http://vllm:8000/metrics")
bottlenecks = client.detect_bottlenecks("vllm-1", metrics)
workflow = client.start_workflow("vllm-1", "vllm")
```

---

## FAQ

**Q: How often should I collect metrics?**  
A: Every 30-60 seconds is recommended for production monitoring.

**Q: Can I run multiple agents?**  
A: Yes, the agent is stateless and can be horizontally scaled.

**Q: What happens if an optimization fails?**  
A: The workflow will automatically rollback to the previous configuration.

**Q: Can I customize bottleneck thresholds?**  
A: Yes, thresholds can be configured via environment variables or config files.

**Q: Does the agent store metrics?**  
A: No, the agent is stateless. Integrate with Prometheus for metrics storage.

---

**Last Updated**: 2024-01-01  
**Version**: 1.0.0
