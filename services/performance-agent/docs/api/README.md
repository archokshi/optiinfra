# Performance Agent API Reference

## Overview

The Performance Agent provides REST APIs for monitoring LLM inference instances, detecting performance bottlenecks, and managing optimization workflows.

## Base URL

```
http://localhost:8002/api/v1
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8002/docs
- **ReDoc**: http://localhost:8002/redoc

## Authentication

Currently no authentication required (development mode).
Production deployments should implement authentication.

---

## Health Endpoints

### GET /health

Basic health check endpoint.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Example**:
```bash
curl http://localhost:8002/api/v1/health
```

---

### GET /health/detailed

Detailed health information including dependencies.

**Response**: `200 OK`

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "dependencies": {
    "database": "healthy",
    "cache": "healthy"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Example**:
```bash
curl http://localhost:8002/api/v1/health/detailed
```

---

## Configuration Endpoints

### GET /config

Get agent configuration and capabilities.

**Response**: `200 OK`

```json
{
  "agent_id": "performance-agent",
  "version": "1.0.0",
  "capabilities": ["vllm", "tgi", "sglang"],
  "polling_interval": 30
}
```

**Example**:
```bash
curl http://localhost:8002/api/v1/config
```

---

### GET /capabilities

Get detailed agent capabilities.

**Response**: `200 OK`

```json
{
  "capabilities": {
    "collectors": ["vllm", "tgi", "sglang"],
    "optimizers": ["kv_cache", "quantization", "batching"],
    "workflows": ["optimization", "analysis"]
  },
  "supported_metrics": [
    "request_metrics",
    "gpu_metrics",
    "throughput_metrics"
  ]
}
```

**Example**:
```bash
curl http://localhost:8002/api/v1/capabilities
```

---

## Metrics Endpoints

### POST /metrics/collect

Collect metrics from an LLM inference instance.

**Request Body**:
```json
{
  "instance_id": "vllm-1",
  "instance_type": "vllm",
  "metrics_url": "http://localhost:8000/metrics"
}
```

**Parameters**:
- `instance_id` (string, required): Unique instance identifier
- `instance_type` (string, required): Instance type (`vllm`, `tgi`, `sglang`)
- `metrics_url` (string, required): Prometheus metrics endpoint URL

**Response**: `200 OK`

```json
{
  "instance_id": "vllm-1",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_metrics": {
    "success_total": 1000,
    "failure_total": 10,
    "time_to_first_token_seconds": 0.05,
    "time_per_output_token_seconds": 0.02,
    "e2e_request_latency_seconds": 1.5
  },
  "gpu_metrics": {
    "cache_usage_perc": 75.5,
    "memory_usage_bytes": 8589934592,
    "num_requests_running": 5,
    "num_requests_waiting": 2
  },
  "throughput_metrics": {
    "tokens_per_second": 500.0,
    "generation_tokens_total": 50000,
    "prompt_tokens_total": 25000
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8002/api/v1/metrics/collect \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-1",
    "instance_type": "vllm",
    "metrics_url": "http://localhost:8000/metrics"
  }'
```

**Error Responses**:
- `400 Bad Request`: Invalid request parameters
- `500 Internal Server Error`: Failed to collect metrics
- `503 Service Unavailable`: Instance not reachable

---

## Analysis Endpoints

### POST /analysis/detect-bottlenecks

Detect performance bottlenecks from collected metrics.

**Request Body**:
```json
{
  "instance_id": "vllm-1",
  "metrics": {
    "request_metrics": {...},
    "gpu_metrics": {...},
    "throughput_metrics": {...}
  }
}
```

**Response**: `200 OK`

```json
{
  "instance_id": "vllm-1",
  "bottlenecks": [
    {
      "type": "MEMORY_PRESSURE",
      "severity": "HIGH",
      "description": "GPU memory usage at 90%, approaching capacity",
      "metric_name": "memory_usage",
      "current_value": 0.9,
      "threshold_value": 0.8,
      "recommendation": "Enable quantization or reduce batch size",
      "detected_at": "2024-01-01T00:00:00Z"
    },
    {
      "type": "HIGH_LATENCY",
      "severity": "MEDIUM",
      "description": "Time to first token exceeds threshold",
      "metric_name": "ttft",
      "current_value": 0.15,
      "threshold_value": 0.1,
      "recommendation": "Optimize KV cache or enable speculative decoding",
      "detected_at": "2024-01-01T00:00:00Z"
    }
  ],
  "analysis_timestamp": "2024-01-01T00:00:00Z"
}
```

**Bottleneck Types**:
- `MEMORY_PRESSURE`: High GPU memory usage
- `HIGH_LATENCY`: Slow response times
- `LOW_THROUGHPUT`: Low tokens per second
- `QUEUE_BUILDUP`: Requests waiting in queue
- `CACHE_INEFFICIENCY`: Low cache hit rate

**Severity Levels**:
- `LOW`: Minor issue, monitor
- `MEDIUM`: Noticeable impact, optimize soon
- `HIGH`: Significant impact, optimize now
- `CRITICAL`: Severe impact, immediate action

**Example**:
```bash
curl -X POST http://localhost:8002/api/v1/analysis/detect-bottlenecks \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-1",
    "metrics": {...}
  }'
```

---

## Optimization Endpoints

### POST /optimization/recommend

Generate optimization recommendations based on bottlenecks.

**Request Body**:
```json
{
  "instance_id": "vllm-1",
  "instance_type": "vllm",
  "bottlenecks": [
    {
      "type": "MEMORY_PRESSURE",
      "severity": "HIGH",
      "description": "High memory usage"
    }
  ],
  "current_config": {
    "max_batch_size": 32,
    "quantization": null
  }
}
```

**Response**: `200 OK`

```json
{
  "instance_id": "vllm-1",
  "optimizations": [
    {
      "type": "QUANTIZATION",
      "priority": "HIGH",
      "description": "Enable INT4 quantization to reduce memory usage by 50%",
      "estimated_improvement": {
        "memory_reduction": 0.5,
        "latency_impact": 0.1
      },
      "config_changes": {
        "quantization": "int4"
      },
      "risks": [
        "Slight accuracy degradation possible",
        "Requires model reload"
      ]
    },
    {
      "type": "KV_CACHE",
      "priority": "MEDIUM",
      "description": "Optimize KV cache block size",
      "estimated_improvement": {
        "memory_reduction": 0.15
      },
      "config_changes": {
        "block_size": 16
      }
    }
  ],
  "recommendation_timestamp": "2024-01-01T00:00:00Z"
}
```

**Optimization Types**:
- `QUANTIZATION`: Model quantization (INT8, INT4)
- `KV_CACHE`: KV cache optimization
- `BATCHING`: Batch size optimization
- `SPECULATIVE_DECODING`: Enable speculative decoding

**Example**:
```bash
curl -X POST http://localhost:8002/api/v1/optimization/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-1",
    "instance_type": "vllm",
    "bottlenecks": [...]
  }'
```

---

## Workflow Endpoints

### POST /workflows

Start an optimization workflow.

**Request Body**:
```json
{
  "instance_id": "vllm-1",
  "instance_type": "vllm",
  "workflow_type": "optimization",
  "auto_approve": false
}
```

**Response**: `201 Created`

```json
{
  "workflow_id": "wf-123e4567-e89b-12d3-a456-426614174000",
  "status": "PENDING_APPROVAL",
  "instance_id": "vllm-1",
  "optimizations": [
    {
      "type": "QUANTIZATION",
      "description": "Enable INT4 quantization"
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "requires_approval": true
}
```

**Workflow Statuses**:
- `PENDING_APPROVAL`: Waiting for approval
- `APPROVED`: Approved, ready to execute
- `REJECTED`: Rejected by operator
- `IN_PROGRESS`: Currently executing
- `COMPLETED`: Successfully completed
- `FAILED`: Execution failed
- `ROLLED_BACK`: Rolled back due to issues

**Example**:
```bash
curl -X POST http://localhost:8002/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d '{
    "instance_id": "vllm-1",
    "instance_type": "vllm",
    "workflow_type": "optimization"
  }'
```

---

### GET /workflows/{workflow_id}

Get workflow status and details.

**Path Parameters**:
- `workflow_id` (string, required): Workflow identifier

**Response**: `200 OK`

```json
{
  "workflow_id": "wf-123e4567-e89b-12d3-a456-426614174000",
  "status": "IN_PROGRESS",
  "instance_id": "vllm-1",
  "current_stage": "CANARY",
  "progress": 0.5,
  "stages": [
    {
      "name": "ANALYSIS",
      "status": "COMPLETED",
      "started_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:01:00Z"
    },
    {
      "name": "CANARY",
      "status": "IN_PROGRESS",
      "started_at": "2024-01-01T00:02:00Z",
      "progress": 0.5
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:02:30Z"
}
```

**Example**:
```bash
curl http://localhost:8002/api/v1/workflows/wf-123e4567-e89b-12d3-a456-426614174000
```

---

### GET /workflows

List all workflows.

**Query Parameters**:
- `status` (string, optional): Filter by status
- `instance_id` (string, optional): Filter by instance
- `limit` (integer, optional): Max results (default: 50)

**Response**: `200 OK`

```json
[
  {
    "workflow_id": "wf-123",
    "status": "COMPLETED",
    "instance_id": "vllm-1",
    "created_at": "2024-01-01T00:00:00Z"
  },
  {
    "workflow_id": "wf-456",
    "status": "IN_PROGRESS",
    "instance_id": "vllm-2",
    "created_at": "2024-01-01T01:00:00Z"
  }
]
```

**Example**:
```bash
curl "http://localhost:8002/api/v1/workflows?status=IN_PROGRESS"
```

---

### POST /workflows/{workflow_id}/approve

Approve a pending workflow.

**Path Parameters**:
- `workflow_id` (string, required): Workflow identifier

**Response**: `200 OK`

```json
{
  "workflow_id": "wf-123",
  "status": "APPROVED",
  "approved_at": "2024-01-01T00:00:00Z",
  "approved_by": "operator"
}
```

**Example**:
```bash
curl -X POST http://localhost:8002/api/v1/workflows/wf-123/approve
```

---

### POST /workflows/{workflow_id}/reject

Reject a pending workflow.

**Path Parameters**:
- `workflow_id` (string, required): Workflow identifier

**Request Body** (optional):
```json
{
  "reason": "Risk too high for production"
}
```

**Response**: `200 OK`

```json
{
  "workflow_id": "wf-123",
  "status": "REJECTED",
  "rejected_at": "2024-01-01T00:00:00Z",
  "rejected_by": "operator",
  "reason": "Risk too high for production"
}
```

**Example**:
```bash
curl -X POST http://localhost:8002/api/v1/workflows/wf-123/reject \
  -H "Content-Type: application/json" \
  -d '{"reason": "Risk too high"}'
```

---

## Error Responses

### Standard Error Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid instance_type",
    "details": {
      "field": "instance_type",
      "allowed_values": ["vllm", "tgi", "sglang"]
    }
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `NOT_FOUND` | 404 | Resource not found |
| `COLLECTION_ERROR` | 500 | Failed to collect metrics |
| `ANALYSIS_ERROR` | 500 | Failed to analyze metrics |
| `WORKFLOW_ERROR` | 500 | Workflow execution failed |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limits

Currently no rate limits in development mode.

Production deployments should implement:
- **Per IP**: 100 requests/minute
- **Per API Key**: 1000 requests/minute

---

## Versioning

API version is included in the URL path: `/api/v1/`

Breaking changes will increment the major version: `/api/v2/`

---

## SDKs and Client Libraries

### Python

```python
import requests

class PerformanceAgentClient:
    def __init__(self, base_url="http://localhost:8002"):
        self.base_url = base_url
    
    def collect_metrics(self, instance_id, instance_type, metrics_url):
        response = requests.post(
            f"{self.base_url}/api/v1/metrics/collect",
            json={
                "instance_id": instance_id,
                "instance_type": instance_type,
                "metrics_url": metrics_url
            }
        )
        return response.json()

# Usage
client = PerformanceAgentClient()
metrics = client.collect_metrics("vllm-1", "vllm", "http://localhost:8000/metrics")
```

---

## Changelog

### v1.0.0 (2024-01-01)
- Initial API release
- Health, config, metrics, analysis, optimization, workflow endpoints
- Support for vLLM, TGI, SGLang

---

**API Version**: 1.0.0  
**Last Updated**: 2024-01-01
