# Cost Agent API Documentation

**Version**: 1.0.0  
**Base URL**: `http://localhost:8001` (development) | `https://api.optiinfra.com` (production)

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Endpoints](#endpoints)
  - [Health & Status](#health--status)
  - [Authentication](#authentication-endpoints)
  - [Cost Collection](#cost-collection)
  - [Analysis](#analysis)
  - [Recommendations](#recommendations)
  - [Execution](#execution)
  - [Learning](#learning)
  - [Bulk Operations](#bulk-operations)
  - [Webhooks](#webhooks)
  - [Notifications](#notifications)
- [Code Examples](#code-examples)

---

## Overview

The Cost Agent API provides comprehensive cost optimization capabilities for cloud infrastructure across AWS, GCP, Azure, and Vultr.

### Key Features

- **Cost Collection**: Automated cost data collection from multiple cloud providers
- **Anomaly Detection**: AI-powered anomaly detection in cost patterns
- **Trend Analysis**: Historical trend analysis and forecasting
- **Recommendations**: Intelligent cost-saving recommendations
- **Execution**: Automated execution with approval workflows
- **Learning Loop**: Continuous learning from execution outcomes

### API Design Principles

- **RESTful**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON**: All requests and responses use JSON
- **Versioned**: API versioned via URL path (`/api/v1`)
- **Authenticated**: Secure authentication via API keys or JWT tokens
- **Rate Limited**: Fair usage policies enforced

---

## Authentication

All protected endpoints require authentication using one of the following methods:

### API Key Authentication

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" \
  https://api.optiinfra.com/api/v1/analyze
```

**Creating an API Key**:
```bash
POST /api/v1/auth/api-key/create
```

### JWT Token Authentication

Include the JWT token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer your-jwt-token-here" \
  https://api.optiinfra.com/api/v1/analyze
```

**Getting a JWT Token**:
```bash
POST /api/v1/auth/token
```

### Public Endpoints

The following endpoints do not require authentication:
- `GET /api/v1/health`
- `GET /api/v1/health/detailed`
- `GET /metrics`

---

## Rate Limiting

Rate limits are enforced per customer and endpoint to ensure fair usage.

### Default Limits

- **Standard Endpoints**: 100 requests per minute
- **Bulk Operations**: 10 requests per minute
- **Analysis Endpoints**: 50 requests per minute

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1634567890
```

### Rate Limit Exceeded

When rate limit is exceeded, the API returns:

```json
{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

**HTTP Status**: `429 Too Many Requests`

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Additional context"
  },
  "request_id": "req-abc123",
  "timestamp": "2025-01-23T19:30:00Z"
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `invalid_request` | Request validation failed |
| 401 | `unauthorized` | Authentication required |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not_found` | Resource not found |
| 409 | `conflict` | Resource conflict |
| 422 | `validation_error` | Input validation failed |
| 429 | `rate_limit_exceeded` | Rate limit exceeded |
| 500 | `internal_error` | Internal server error |
| 503 | `service_unavailable` | Service temporarily unavailable |

---

## Endpoints

### Health & Status

#### GET /api/v1/health

Basic health check endpoint.

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-23T19:30:00Z",
  "version": "1.0.0",
  "agent_id": "cost-agent-001",
  "agent_type": "cost",
  "uptime_seconds": 3600.5
}
```

**Example**:
```bash
curl http://localhost:8001/api/v1/health
```

---

#### GET /api/v1/health/detailed

Detailed health check with component status.

**Authentication**: Not required

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-23T19:30:00Z",
  "version": "1.0.0",
  "components": {
    "database": {
      "status": "healthy",
      "latency_ms": 5.2
    },
    "cache": {
      "status": "healthy",
      "latency_ms": 1.1
    },
    "aws_api": {
      "status": "healthy",
      "latency_ms": 150.3
    },
    "gcp_api": {
      "status": "healthy",
      "latency_ms": 120.5
    }
  }
}
```

---

#### GET /metrics

Prometheus metrics endpoint.

**Authentication**: Not required

**Response**: Prometheus text format

---

### Authentication Endpoints

#### POST /api/v1/auth/api-key/create

Create a new API key.

**Authentication**: Required (JWT token)

**Request**:
```json
{
  "customer_id": "customer-123",
  "name": "Production API Key",
  "expires_in_days": 365
}
```

**Response**:
```json
{
  "api_key": "ak_live_1234567890abcdef",
  "key_id": "key-abc123",
  "customer_id": "customer-123",
  "name": "Production API Key",
  "created_at": "2025-01-23T19:30:00Z",
  "expires_at": "2026-01-23T19:30:00Z"
}
```

---

#### POST /api/v1/auth/token

Generate JWT authentication token.

**Authentication**: Not required (uses credentials)

**Request**:
```json
{
  "customer_id": "customer-123",
  "secret": "customer-secret-key"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "customer_id": "customer-123"
}
```

---

#### DELETE /api/v1/auth/api-key/{key_id}

Revoke an API key.

**Authentication**: Required

**Response**:
```json
{
  "success": true,
  "message": "API key revoked successfully",
  "key_id": "key-abc123"
}
```

---

### Cost Collection

#### POST /api/v1/aws/costs/collect

Collect AWS cost data.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "granularity": "DAILY",
  "group_by": ["SERVICE", "REGION"],
  "filters": {
    "tags": {
      "Environment": "production"
    }
  }
}
```

**Response**:
```json
{
  "request_id": "req-abc123",
  "customer_id": "customer-123",
  "timestamp": "2025-01-23T19:30:00Z",
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "total_cost": 15234.56,
  "currency": "USD",
  "data_points": 31,
  "costs": [
    {
      "date": "2025-01-01",
      "service": "EC2",
      "region": "us-east-1",
      "cost": 450.23,
      "usage": {
        "hours": 720,
        "instances": 10
      }
    }
  ],
  "summary": {
    "by_service": {
      "EC2": 8500.00,
      "S3": 2300.00,
      "RDS": 4434.56
    },
    "by_region": {
      "us-east-1": 10000.00,
      "us-west-2": 5234.56
    }
  }
}
```

---

#### POST /api/v1/gcp/costs/collect

Collect GCP cost data.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "project_id": "my-gcp-project",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "services": ["compute", "storage", "bigquery"]
}
```

**Response**: Similar to AWS costs response

---

#### POST /api/v1/azure/costs/collect

Collect Azure cost data.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "subscription_id": "sub-123",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "resource_groups": ["production", "staging"]
}
```

**Response**: Similar to AWS costs response

---

### Analysis

#### POST /api/v1/analyze

Analyze costs and detect anomalies.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "provider": "aws",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "analysis_types": ["anomaly", "trend", "forecast"],
  "sensitivity": "medium"
}
```

**Response**:
```json
{
  "request_id": "req-abc123",
  "customer_id": "customer-123",
  "timestamp": "2025-01-23T19:30:00Z",
  "analysis_period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "anomalies": [
    {
      "anomaly_id": "anom-xyz789",
      "date": "2025-01-15",
      "service": "EC2",
      "region": "us-east-1",
      "expected_cost": 450.00,
      "actual_cost": 890.00,
      "deviation_percent": 97.8,
      "severity": "high",
      "confidence": 0.95,
      "description": "Unusual spike in EC2 costs detected"
    }
  ],
  "trends": [
    {
      "metric": "total_cost",
      "direction": "increasing",
      "rate_of_change": 15.5,
      "confidence": 0.88,
      "description": "Total costs increasing at 15.5% per month"
    }
  ],
  "forecast": {
    "next_month": {
      "predicted_cost": 17500.00,
      "confidence_interval": {
        "lower": 16000.00,
        "upper": 19000.00
      },
      "confidence": 0.85
    }
  },
  "summary": "Detected 3 anomalies and identified upward cost trend"
}
```

---

### Recommendations

#### POST /api/v1/recommendations/generate

Generate cost optimization recommendations.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "provider": "aws",
  "recommendation_types": ["spot", "reserved_instances", "right_sizing"],
  "min_savings": 100.00,
  "risk_tolerance": "medium"
}
```

**Response**:
```json
{
  "request_id": "req-abc123",
  "customer_id": "customer-123",
  "timestamp": "2025-01-23T19:30:00Z",
  "total_recommendations": 15,
  "total_potential_savings": 5234.56,
  "recommendations": [
    {
      "recommendation_id": "rec-xyz789",
      "type": "spot_migration",
      "priority": "high",
      "resource_id": "i-1234567890abcdef0",
      "resource_type": "ec2_instance",
      "current_cost": 150.00,
      "estimated_savings": 60.00,
      "savings_percent": 40.0,
      "confidence_score": 0.92,
      "risk_level": "low",
      "implementation_effort": "low",
      "description": "Migrate on-demand instance to spot instance",
      "implementation_steps": [
        "Create spot instance request",
        "Migrate workload gradually",
        "Monitor for interruptions",
        "Update auto-scaling configuration"
      ],
      "prerequisites": [
        "Workload must be fault-tolerant",
        "Auto-scaling group configured"
      ],
      "estimated_implementation_time": "2 hours"
    }
  ],
  "summary": {
    "by_type": {
      "spot_migration": {
        "count": 6,
        "total_savings": 2400.00
      },
      "reserved_instances": {
        "count": 5,
        "total_savings": 1834.56
      },
      "right_sizing": {
        "count": 4,
        "total_savings": 1000.00
      }
    },
    "by_priority": {
      "high": 8,
      "medium": 5,
      "low": 2
    }
  }
}
```

---

#### GET /api/v1/recommendations/{recommendation_id}

Get details of a specific recommendation.

**Authentication**: Required

**Response**:
```json
{
  "recommendation_id": "rec-xyz789",
  "type": "spot_migration",
  "status": "pending",
  "created_at": "2025-01-23T19:30:00Z",
  "resource_id": "i-1234567890abcdef0",
  "estimated_savings": 60.00,
  "confidence_score": 0.92,
  "implementation_steps": [...],
  "execution_history": []
}
```

---

#### POST /api/v1/recommendations/{recommendation_id}/approve

Approve a recommendation for execution.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "approved_by": "user@example.com",
  "notes": "Approved for production deployment"
}
```

**Response**:
```json
{
  "recommendation_id": "rec-xyz789",
  "status": "approved",
  "approved_at": "2025-01-23T19:30:00Z",
  "approved_by": "user@example.com",
  "execution_scheduled": true,
  "scheduled_time": "2025-01-24T02:00:00Z"
}
```

---

### Execution

#### POST /api/v1/execution/execute

Execute an approved recommendation.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "recommendation_id": "rec-xyz789",
  "execution_mode": "gradual",
  "rollout_strategy": {
    "phases": [
      {"percentage": 10, "duration_minutes": 30},
      {"percentage": 50, "duration_minutes": 60},
      {"percentage": 100, "duration_minutes": 0}
    ]
  },
  "auto_rollback": true,
  "rollback_threshold": {
    "error_rate": 0.05,
    "performance_degradation": 0.10
  }
}
```

**Response**:
```json
{
  "execution_id": "exec-abc123",
  "recommendation_id": "rec-xyz789",
  "customer_id": "customer-123",
  "status": "in_progress",
  "started_at": "2025-01-23T19:30:00Z",
  "current_phase": 1,
  "total_phases": 3,
  "progress_percent": 10,
  "metrics": {
    "resources_modified": 1,
    "resources_total": 10,
    "error_rate": 0.0,
    "performance_impact": 0.02
  },
  "estimated_completion": "2025-01-23T21:00:00Z"
}
```

---

#### GET /api/v1/execution/{execution_id}/status

Get execution status.

**Authentication**: Required

**Response**:
```json
{
  "execution_id": "exec-abc123",
  "status": "completed",
  "started_at": "2025-01-23T19:30:00Z",
  "completed_at": "2025-01-23T21:00:00Z",
  "duration_minutes": 90,
  "phases_completed": 3,
  "total_phases": 3,
  "success": true,
  "resources_modified": 10,
  "actual_savings": 58.50,
  "estimated_savings": 60.00,
  "savings_accuracy": 0.975,
  "rollback_triggered": false,
  "metrics": {
    "error_rate": 0.01,
    "performance_impact": 0.03,
    "quality_score": 0.97
  }
}
```

---

#### POST /api/v1/execution/{execution_id}/rollback

Rollback an execution.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "reason": "Performance degradation detected",
  "rollback_mode": "immediate"
}
```

**Response**:
```json
{
  "execution_id": "exec-abc123",
  "rollback_id": "rollback-xyz789",
  "status": "rolling_back",
  "started_at": "2025-01-23T20:00:00Z",
  "estimated_completion": "2025-01-23T20:15:00Z",
  "resources_to_restore": 10
}
```

---

### Learning

#### POST /api/v1/learning/feedback

Submit feedback on execution outcome.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "execution_id": "exec-abc123",
  "feedback_type": "outcome",
  "rating": 4,
  "actual_savings": 58.50,
  "quality_metrics": {
    "performance_impact": 0.03,
    "stability": 0.98,
    "user_satisfaction": 4.5
  },
  "comments": "Execution went smoothly, minor performance impact as expected"
}
```

**Response**:
```json
{
  "feedback_id": "feedback-abc123",
  "execution_id": "exec-abc123",
  "recorded_at": "2025-01-23T21:00:00Z",
  "learning_applied": true,
  "model_updated": true,
  "confidence_adjustment": 0.02
}
```

---

#### GET /api/v1/learning/insights

Get learning insights and improvements.

**Authentication**: Required

**Response**:
```json
{
  "customer_id": "customer-123",
  "timestamp": "2025-01-23T19:30:00Z",
  "total_executions": 150,
  "success_rate": 0.94,
  "average_savings_accuracy": 0.92,
  "insights": [
    {
      "insight_type": "pattern",
      "description": "Spot migrations most successful during off-peak hours",
      "confidence": 0.88,
      "recommendation": "Schedule spot migrations between 2 AM - 6 AM"
    },
    {
      "insight_type": "improvement",
      "description": "Right-sizing recommendations 15% more accurate after model update",
      "impact": "high"
    }
  ],
  "model_performance": {
    "accuracy": 0.92,
    "precision": 0.89,
    "recall": 0.94,
    "f1_score": 0.91
  }
}
```

---

### Bulk Operations

#### POST /api/v1/bulk/analyze

Analyze multiple resources in bulk.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "resources": [
    {
      "provider": "aws",
      "resource_type": "ec2",
      "resource_id": "i-123"
    },
    {
      "provider": "gcp",
      "resource_type": "compute",
      "resource_id": "instance-456"
    }
  ],
  "analysis_types": ["cost", "utilization", "recommendations"]
}
```

**Response**:
```json
{
  "bulk_operation_id": "bulk-abc123",
  "status": "processing",
  "total_resources": 2,
  "processed": 0,
  "estimated_completion": "2025-01-23T19:35:00Z"
}
```

---

### Webhooks

#### POST /api/v1/webhooks/register

Register a webhook for events.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "url": "https://your-app.com/webhooks/cost-agent",
  "events": [
    "recommendation.created",
    "execution.completed",
    "anomaly.detected"
  ],
  "secret": "webhook-secret-key"
}
```

**Response**:
```json
{
  "webhook_id": "webhook-abc123",
  "url": "https://your-app.com/webhooks/cost-agent",
  "events": [...],
  "created_at": "2025-01-23T19:30:00Z",
  "status": "active"
}
```

---

### Notifications

#### POST /api/v1/notifications/subscribe

Subscribe to notifications.

**Authentication**: Required

**Request**:
```json
{
  "customer_id": "customer-123",
  "channel": "email",
  "address": "alerts@example.com",
  "notification_types": [
    "anomaly_detected",
    "high_value_recommendation",
    "execution_failed"
  ],
  "frequency": "immediate"
}
```

**Response**:
```json
{
  "subscription_id": "sub-abc123",
  "channel": "email",
  "address": "alerts@example.com",
  "status": "active",
  "created_at": "2025-01-23T19:30:00Z"
}
```

---

## Code Examples

### Python

```python
import requests

# Configuration
API_KEY = "your-api-key-here"
BASE_URL = "http://localhost:8001"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Collect AWS costs
response = requests.post(
    f"{BASE_URL}/api/v1/aws/costs/collect",
    headers=headers,
    json={
        "customer_id": "customer-123",
        "start_date": "2025-01-01",
        "end_date": "2025-01-31",
        "granularity": "DAILY"
    }
)

costs = response.json()
print(f"Total cost: ${costs['total_cost']}")

# Generate recommendations
response = requests.post(
    f"{BASE_URL}/api/v1/recommendations/generate",
    headers=headers,
    json={
        "customer_id": "customer-123",
        "provider": "aws",
        "recommendation_types": ["spot", "right_sizing"]
    }
)

recommendations = response.json()
print(f"Found {len(recommendations['recommendations'])} recommendations")
print(f"Potential savings: ${recommendations['total_potential_savings']}")
```

### JavaScript

```javascript
const axios = require('axios');

const API_KEY = 'your-api-key-here';
const BASE_URL = 'http://localhost:8001';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Analyze costs
async function analyzeCosts() {
  const response = await axios.post(
    `${BASE_URL}/api/v1/analyze`,
    {
      customer_id: 'customer-123',
      provider: 'aws',
      start_date: '2025-01-01',
      end_date: '2025-01-31',
      analysis_types: ['anomaly', 'trend']
    },
    { headers }
  );
  
  const analysis = response.data;
  console.log(`Detected ${analysis.anomalies.length} anomalies`);
  return analysis;
}

analyzeCosts();
```

### cURL

```bash
# Health check
curl http://localhost:8001/api/v1/health

# Generate recommendations
curl -X POST http://localhost:8001/api/v1/recommendations/generate \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-123",
    "provider": "aws",
    "recommendation_types": ["spot", "reserved_instances", "right_sizing"]
  }'

# Execute recommendation
curl -X POST http://localhost:8001/api/v1/execution/execute \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "customer-123",
    "recommendation_id": "rec-xyz789",
    "execution_mode": "gradual",
    "auto_rollback": true
  }'
```

---

## Support

- **Documentation**: https://docs.optiinfra.com
- **API Status**: https://status.optiinfra.com
- **Support Email**: support@optiinfra.com
- **GitHub Issues**: https://github.com/optiinfra/cost-agent/issues

---

**Last Updated**: 2025-01-23  
**API Version**: 1.0.0
