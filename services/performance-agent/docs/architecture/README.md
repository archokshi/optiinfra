# Performance Agent Architecture

## System Overview

The Performance Agent is a microservice that monitors LLM inference instances, detects performance bottlenecks, and orchestrates optimization workflows. It's built with FastAPI and follows a modular, event-driven architecture.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Performance Agent                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Collectors  │  │   Analysis   │  │  Optimizers  │         │
│  │              │  │    Engine    │  │              │         │
│  │ - vLLM       │  │              │  │ - KV Cache   │         │
│  │ - TGI        │  │ - Bottleneck │  │ - Quantize   │         │
│  │ - SGLang     │  │   Detector   │  │ - Batching   │         │
│  │              │  │ - SLO Monitor│  │              │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
│         │                  │                  │                 │
│         └──────────────────┼──────────────────┘                 │
│                            │                                    │
│                   ┌────────▼────────┐                           │
│                   │    Workflow     │                           │
│                   │     Manager     │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
│                   ┌────────▼────────┐                           │
│                   │   FastAPI       │                           │
│                   │   REST API      │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
         ┌────▼────┐   ┌─────▼─────┐  ┌────▼────┐
         │  vLLM   │   │    TGI    │  │ SGLang  │
         │Instance │   │ Instance  │  │Instance │
         └─────────┘   └───────────┘  └─────────┘
              │              │              │
         ┌────▼────────────────▼──────────────▼────┐
         │         Orchestrator Service            │
         └─────────────────────────────────────────┘
```

## Core Components

### 1. Collectors

**Purpose**: Collect metrics from LLM inference instances

**Components**:
- `VLLMCollector`: Collects metrics from vLLM instances
- `TGICollector`: Collects metrics from TGI instances
- `SGLangCollector`: Collects metrics from SGLang instances
- `PrometheusParser`: Parses Prometheus text format

**Responsibilities**:
- Poll Prometheus metrics endpoints
- Parse metrics into structured format
- Handle connection errors and timeouts
- Support async operations

**Metrics Collected**:
```python
{
    "request_metrics": {
        "success_total": int,
        "failure_total": int,
        "time_to_first_token_seconds": float,
        "time_per_output_token_seconds": float,
        "e2e_request_latency_seconds": float
    },
    "gpu_metrics": {
        "cache_usage_perc": float,
        "memory_usage_bytes": int,
        "num_requests_running": int,
        "num_requests_waiting": int
    },
    "throughput_metrics": {
        "tokens_per_second": float,
        "generation_tokens_total": int,
        "prompt_tokens_total": int
    }
}
```

### 2. Analysis Engine

**Purpose**: Analyze metrics to detect performance issues

**Components**:
- `BottleneckDetector`: Detects performance bottlenecks
- `SLOMonitor`: Monitors SLO compliance
- `AnalysisEngine`: Orchestrates analysis

**Bottleneck Types**:
- **MEMORY_PRESSURE**: High GPU memory usage
- **HIGH_LATENCY**: Slow response times
- **LOW_THROUGHPUT**: Low tokens per second
- **QUEUE_BUILDUP**: Requests waiting in queue
- **CACHE_INEFFICIENCY**: Low cache hit rate

**Detection Logic**:
```python
# Example: Memory pressure detection
if gpu_memory_usage > 0.8:
    bottleneck = Bottleneck(
        type=BottleneckType.MEMORY_PRESSURE,
        severity=Severity.HIGH if usage > 0.9 else Severity.MEDIUM,
        description=f"GPU memory at {usage*100}%",
        recommendation="Enable quantization"
    )
```

### 3. Optimization Engine

**Purpose**: Generate optimization recommendations

**Components**:
- `KVCacheOptimizer`: Optimize KV cache settings
- `QuantizationOptimizer`: Recommend quantization
- `BatchingOptimizer`: Optimize batch sizes
- `OptimizationEngine`: Orchestrates optimization

**Optimization Strategies**:

#### KV Cache Optimization
- Adjust block size
- Tune cache size
- Enable/disable prefix caching

#### Quantization
- INT8 for moderate memory savings
- INT4 for aggressive memory savings
- Consider accuracy vs. performance tradeoff

#### Batching
- Increase batch size for throughput
- Decrease for latency
- Consider queue depth

### 4. Workflow Manager

**Purpose**: Manage optimization workflows with approval gates

**Workflow Stages**:
1. **Analysis**: Collect and analyze metrics
2. **Recommendation**: Generate optimizations
3. **Approval**: Wait for operator approval
4. **Canary**: Deploy to small percentage
5. **Validation**: Validate performance
6. **Rollout**: Gradual rollout to all instances
7. **Completion**: Finalize and cleanup

**State Machine**:
```
PENDING_APPROVAL → APPROVED → IN_PROGRESS → COMPLETED
                 ↓                        ↓
              REJECTED                 FAILED
                                         ↓
                                    ROLLED_BACK
```

### 5. FastAPI Layer

**Purpose**: Expose REST APIs

**Features**:
- OpenAPI/Swagger documentation
- Request validation (Pydantic)
- Error handling
- CORS support
- Health checks

## Data Flow

### Metrics Collection Flow

```
1. API Request → /metrics/collect
2. Collector selects appropriate collector (vLLM/TGI/SGLang)
3. HTTP GET to instance metrics endpoint
4. Parse Prometheus format
5. Extract metrics into structured format
6. Return metrics to caller
```

### Analysis Flow

```
1. API Request → /analysis/detect-bottlenecks
2. BottleneckDetector analyzes metrics
3. Check thresholds for each metric
4. Generate bottleneck objects
5. Prioritize by severity
6. Return bottlenecks with recommendations
```

### Optimization Flow

```
1. API Request → /optimization/recommend
2. OptimizationEngine receives bottlenecks
3. Each optimizer evaluates bottlenecks
4. Generate optimization recommendations
5. Estimate impact and risks
6. Prioritize recommendations
7. Return optimizations
```

### Workflow Flow

```
1. API Request → /workflows (start)
2. Collect metrics
3. Detect bottlenecks
4. Generate recommendations
5. Create workflow (PENDING_APPROVAL)
6. Wait for approval
7. On approval → Execute stages
   - Canary deployment
   - Validation
   - Gradual rollout
8. Complete or rollback
```

## Integration Points

### 1. LLM Inference Instances

**Protocol**: HTTP
**Endpoint**: `/metrics` (Prometheus format)
**Polling**: Every 30-60 seconds

**Supported Instances**:
- vLLM (v0.2.0+)
- TGI (v1.0.0+)
- SGLang (v0.1.0+)

### 2. Orchestrator Service

**Protocol**: REST API
**Purpose**: Workflow coordination and approval

**Interactions**:
- Request workflow approval
- Report workflow status
- Coordinate deployments
- Handle rollbacks

### 3. Prometheus (Optional)

**Protocol**: HTTP
**Purpose**: Metrics storage and querying

**Integration**:
- Agent exposes `/metrics` endpoint
- Prometheus scrapes agent metrics
- Grafana visualizes metrics

## Configuration

### Environment Variables

```bash
# Agent Configuration
AGENT_ID=performance-agent
AGENT_VERSION=1.0.0

# Orchestrator
ORCHESTRATOR_URL=http://orchestrator:8080

# Polling
POLLING_INTERVAL=30
METRICS_TIMEOUT=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Server
PORT=8002
WORKERS=4
```

### Thresholds Configuration

```python
THRESHOLDS = {
    "memory_usage": 0.8,      # 80% memory usage
    "ttft": 0.1,              # 100ms time to first token
    "throughput": 100.0,      # 100 tokens/sec
    "queue_depth": 10,        # 10 waiting requests
    "cache_hit_rate": 0.7     # 70% cache hit rate
}
```

## Scalability

### Horizontal Scaling

The agent is stateless and can be horizontally scaled:

```yaml
# Kubernetes deployment
replicas: 3
```

**Load Balancing**:
- Round-robin across instances
- Health check based routing
- Session affinity not required

### Performance Characteristics

- **Response Time**: 8-15ms (p50)
- **Throughput**: 100+ req/s per instance
- **Concurrent Requests**: 100+ concurrent
- **Memory**: ~200MB per instance
- **CPU**: ~0.5 core per instance

### Async Operations

All I/O operations are async:
```python
async def collect_metrics(self, instance_id, metrics_url):
    async with httpx.AsyncClient() as client:
        response = await client.get(metrics_url)
        return self._parse_metrics(response.text)
```

## Reliability

### Error Handling

- **Retries**: Automatic retry with exponential backoff
- **Timeouts**: Configurable timeouts for all operations
- **Circuit Breaker**: Prevent cascading failures
- **Graceful Degradation**: Continue with partial data

### Health Checks

- **Liveness**: `/api/v1/health`
- **Readiness**: `/api/v1/health/detailed`

### Monitoring

**Metrics Exposed**:
- `performance_agent_requests_total`
- `performance_agent_request_duration_seconds`
- `performance_agent_errors_total`
- `performance_agent_workflows_active`

## Security

### Current State (Development)
- No authentication
- No authorization
- No encryption

### Production Recommendations
- **Authentication**: API keys or OAuth2
- **Authorization**: Role-based access control
- **Encryption**: TLS for all communications
- **Rate Limiting**: Prevent abuse
- **Input Validation**: Strict validation (already implemented)

## Testing Strategy

### Unit Tests (134 tests)
- Test individual components
- Mock external dependencies
- Fast execution (< 1 minute)

### Integration Tests
- Test component interactions
- Use test fixtures
- Medium execution (2-5 minutes)

### Performance Tests (15 tests)
- Load testing (100-500 concurrent)
- Benchmark response times
- Stress testing
- Slow execution (5-10 minutes)

## Technology Stack

- **Framework**: FastAPI 0.104+
- **Language**: Python 3.11+
- **HTTP Client**: httpx (async)
- **Validation**: Pydantic v2
- **Testing**: pytest, pytest-asyncio
- **Metrics**: Prometheus client
- **Logging**: structlog

## Design Patterns

### 1. Strategy Pattern
Different collectors for different instance types:
```python
collectors = {
    "vllm": VLLMCollector(),
    "tgi": TGICollector(),
    "sglang": SGLangCollector()
}
collector = collectors[instance_type]
```

### 2. Factory Pattern
Create optimizers based on bottleneck type:
```python
def create_optimizer(bottleneck_type):
    if bottleneck_type == "MEMORY_PRESSURE":
        return QuantizationOptimizer()
    elif bottleneck_type == "QUEUE_BUILDUP":
        return BatchingOptimizer()
```

### 3. Observer Pattern
Workflow status updates notify observers:
```python
workflow.add_observer(orchestrator)
workflow.update_status("IN_PROGRESS")
```

## Future Enhancements

1. **ML-Based Prediction**: Predict bottlenecks before they occur
2. **Multi-Region Support**: Coordinate across regions
3. **Cost Optimization**: Integrate with cost agent
4. **Auto-Scaling**: Automatic instance scaling
5. **Advanced Workflows**: Complex multi-stage workflows

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-01
