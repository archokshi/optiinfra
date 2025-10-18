# API Reference

## Orchestrator API

Base URL: `http://localhost:8080/api/v1`

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-10-17T12:00:00Z"
}
```

### Agent Registry

#### Register Agent
```http
POST /agents/register
```

**Request**:
```json
{
  "agent_id": "cost-agent-1",
  "agent_type": "cost",
  "capabilities": ["spot_migration", "right_sizing"],
  "endpoint": "http://cost-agent:8001"
}
```

#### List Agents
```http
GET /agents
```

### Workflows

#### Create Workflow
```http
POST /workflows
```

**Request**:
```json
{
  "workflow_type": "spot_migration",
  "customer_id": "customer-123",
  "parameters": {
    "instance_ids": ["i-123", "i-456"]
  }
}
```

#### Get Workflow
```http
GET /workflows/:id
```

## Cost Agent API

Base URL: `http://localhost:8001/api/v1`

### Analysis

```http
POST /analyze
```

**Request**:
```json
{
  "customer_id": "customer-123",
  "time_range": "7d"
}
```

### Recommendations

```http
GET /recommendations
POST /recommendations/:id/approve
POST /recommendations/:id/reject
```

## Performance Agent API

Base URL: `http://localhost:8002/api/v1`

### Analysis

```http
POST /analyze
```

### Optimizations

```http
GET /optimizations
POST /optimizations
```

## Resource Agent API

Base URL: `http://localhost:8003/api/v1`

### Resource Metrics

```http
GET /metrics
```

### Scaling Recommendations

```http
GET /scaling/recommendations
```

## Application Agent API

Base URL: `http://localhost:8004/api/v1`

### Quality Metrics

```http
GET /quality/metrics
```

### Baselines

```http
POST /baselines
GET /baselines/:id
```

### Validation

```http
POST /validate
```

**Request**:
```json
{
  "change_id": "change-123",
  "baseline_id": "baseline-456"
}
```

## Common Response Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error
