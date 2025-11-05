# PHASE2-2.8 PART1: REST APIs - Code Implementation Plan

**Phase**: PHASE2-2.8  
**Agent**: Performance Agent  
**Objective**: Complete and consolidate all REST API endpoints with comprehensive documentation  
**Estimated Time**: 20+15m (35 minutes total)  
**Priority**: HIGH  
**Dependencies**: PHASE2-2.7, 2.6, 2.5, 2.4, 2.3, 2.2

---

## Overview

This phase consolidates and completes all REST API endpoints for the Performance Agent, ensuring comprehensive API documentation, proper error handling, request validation, and OpenAPI/Swagger documentation.

---

## Current API Status

### Existing Endpoints

We already have these API endpoints implemented:

#### 1. Health Endpoints (`src/api/health.py`)
- `GET /api/v1/health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with dependencies
- `GET /api/v1/health/ready` - Readiness probe

#### 2. Metrics Collection Endpoints (`src/api/metrics.py`)
- `POST /api/v1/collect/vllm` - Collect vLLM metrics
- `POST /api/v1/collect/tgi` - Collect TGI metrics
- `POST /api/v1/collect/sglang` - Collect SGLang metrics

#### 3. Analysis Endpoints (`src/api/analysis.py`)
- `POST /api/v1/analyze` - Analyze instance performance

#### 4. Optimization Endpoints (`src/api/optimization.py`)
- `POST /api/v1/optimize` - Generate optimization plan

#### 5. Workflow Endpoints (`src/api/workflows.py`)
- `POST /api/v1/workflows` - Start optimization workflow
- `GET /api/v1/workflows/{workflow_id}` - Get workflow status
- `POST /api/v1/workflows/{workflow_id}/approve` - Approve workflow
- `POST /api/v1/workflows/{workflow_id}/reject` - Reject workflow

**Total**: 12 endpoints across 5 modules

---

## What's Missing

### 1. Comprehensive Error Handling
- Standardized error response format
- Proper HTTP status codes
- Error logging and tracking

### 2. Request Validation
- Input validation middleware
- Request size limits
- Rate limiting (optional)

### 3. API Documentation
- Complete OpenAPI/Swagger documentation
- Request/response examples
- Error response documentation

### 4. Additional Utility Endpoints
- Metrics history endpoint
- Workflow list endpoint
- Configuration endpoint

---

## Implementation Plan

### Step 1: Error Response Models (3 minutes)

#### 1.1 Create src/models/errors.py

```python
"""
Error Response Models

Standardized error responses for API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ErrorDetail(BaseModel):
    """Detailed error information."""
    
    field: Optional[str] = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: Optional[str] = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    path: Optional[str] = Field(None, description="Request path")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response."""
    
    error: str = "validation_error"
    invalid_fields: List[str] = Field(default_factory=list)
```

---

### Step 2: Error Handlers (5 minutes)

#### 2.1 Create src/api/error_handlers.py

```python
"""
Error Handlers

Global error handlers for FastAPI application.
"""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from src.models.errors import ErrorResponse, ErrorDetail, ValidationErrorResponse

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors."""
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    details = []
    invalid_fields = []
    
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        invalid_fields.append(field)
        details.append(ErrorDetail(
            field=field,
            message=error["msg"],
            type=error["type"]
        ))
    
    error_response = ValidationErrorResponse(
        message="Request validation failed",
        details=details,
        invalid_fields=invalid_fields,
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    
    error_response = ErrorResponse(
        error="internal_server_error",
        message="An unexpected error occurred",
        path=str(request.url.path)
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle HTTP exceptions."""
    from fastapi import HTTPException
    
    if isinstance(exc, HTTPException):
        error_response = ErrorResponse(
            error=exc.detail if isinstance(exc.detail, str) else "http_error",
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            path=str(request.url.path)
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump()
        )
    
    return await general_exception_handler(request, exc)
```

---

### Step 3: Additional Utility Endpoints (5 minutes)

#### 3.1 Add to src/api/metrics.py

```python
@router.get(
    "/history/{instance_id}",
    response_model=List[Dict[str, Any]],
    tags=["metrics"]
)
async def get_metrics_history(
    instance_id: str,
    hours: int = 24,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Get metrics history for an instance.
    
    Args:
        instance_id: Instance identifier
        hours: Number of hours of history (default 24)
        limit: Maximum number of data points (default 100)
        
    Returns:
        List of historical metrics
    """
    # This would query from a time-series database in production
    # For now, return empty list
    logger.info(f"Fetching {hours}h of metrics history for {instance_id}")
    return []
```

#### 3.2 Add to src/api/workflows.py

```python
@router.get(
    "/workflows",
    response_model=List[WorkflowState],
    tags=["workflows"]
)
def list_workflows(
    status: Optional[str] = None,
    limit: int = 50
) -> List[WorkflowState]:
    """
    List all workflows.
    
    Args:
        status: Filter by status (optional)
        limit: Maximum number of workflows to return
        
    Returns:
        List of workflows
    """
    workflows = []
    
    for workflow_id, state_dict in workflow_manager.workflows.items():
        state = workflow_manager.get_workflow(workflow_id)
        if state:
            if status is None or state.status.value == status:
                workflows.append(state)
    
    # Sort by created_at descending
    workflows.sort(key=lambda w: w.created_at, reverse=True)
    
    return workflows[:limit]
```

#### 3.3 Create src/api/config.py

```python
"""
Configuration Endpoints

API endpoints for agent configuration.
"""

from fastapi import APIRouter
import logging
from typing import Dict, Any

from src.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/config",
    response_model=Dict[str, Any],
    tags=["config"]
)
def get_config() -> Dict[str, Any]:
    """
    Get agent configuration.
    
    Returns:
        Agent configuration (non-sensitive values only)
    """
    return {
        "agent_name": settings.agent_name,
        "agent_type": settings.agent_type,
        "port": settings.port,
        "log_level": settings.log_level,
        "environment": settings.environment,
        "version": "0.1.0"
    }


@router.get(
    "/capabilities",
    response_model=Dict[str, Any],
    tags=["config"]
)
def get_capabilities() -> Dict[str, Any]:
    """
    Get agent capabilities.
    
    Returns:
        Agent capabilities and supported features
    """
    return {
        "capabilities": [
            "performance_monitoring",
            "bottleneck_detection",
            "slo_monitoring",
            "optimization_recommendations",
            "gradual_rollout",
            "automatic_rollback"
        ],
        "supported_platforms": ["vllm", "tgi", "sglang"],
        "optimization_types": ["kv_cache", "quantization", "batching"],
        "workflow_features": [
            "gradual_rollout",
            "health_monitoring",
            "automatic_rollback",
            "human_approval"
        ]
    }
```

---

### Step 4: Update Main App with Error Handlers (2 minutes)

#### 4.1 Update src/main.py

```python
from fastapi.exceptions import RequestValidationError
from src.api.error_handlers import (
    validation_exception_handler,
    general_exception_handler,
    http_exception_handler
)

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include config router
from src.api import config
app.include_router(config.router, prefix="/api/v1", tags=["config"])
```

---

### Step 5: Enhanced OpenAPI Documentation (5 minutes)

#### 5.1 Update src/main.py OpenAPI Configuration

```python
app = FastAPI(
    title="OptiInfra Performance Agent API",
    description="""
    # OptiInfra Performance Agent API
    
    The Performance Agent optimizes latency and throughput for LLM infrastructure.
    
    ## Features
    
    ### 🔍 Performance Monitoring
    - Collect metrics from vLLM, TGI, and SGLang
    - Real-time performance tracking
    - Historical metrics analysis
    
    ### 🎯 Bottleneck Detection
    - Identify 6 types of performance bottlenecks
    - Severity assessment (LOW, MEDIUM, HIGH, CRITICAL)
    - Actionable recommendations
    
    ### 📊 SLO Monitoring
    - Flexible SLO target configuration
    - Compliance tracking
    - Alert generation
    
    ### ⚡ Optimization Engine
    - KV cache optimization
    - Quantization recommendations (INT8, INT4, FP8)
    - Batch size tuning
    - Impact estimation
    
    ### 🔄 Gradual Rollout Workflow
    - LangGraph-powered state machine
    - 10% → 50% → 100% deployment
    - Health monitoring between stages
    - Automatic rollback on degradation
    - Human approval gates
    
    ## API Endpoints
    
    ### Health & Status
    - `GET /api/v1/health` - Basic health check
    - `GET /api/v1/health/detailed` - Detailed health
    - `GET /api/v1/health/ready` - Readiness probe
    
    ### Metrics Collection
    - `POST /api/v1/collect/vllm` - Collect vLLM metrics
    - `POST /api/v1/collect/tgi` - Collect TGI metrics
    - `POST /api/v1/collect/sglang` - Collect SGLang metrics
    - `GET /api/v1/history/{instance_id}` - Get metrics history
    
    ### Analysis
    - `POST /api/v1/analyze` - Analyze performance
    
    ### Optimization
    - `POST /api/v1/optimize` - Generate optimization plan
    
    ### Workflows
    - `POST /api/v1/workflows` - Start workflow
    - `GET /api/v1/workflows` - List workflows
    - `GET /api/v1/workflows/{id}` - Get workflow status
    - `POST /api/v1/workflows/{id}/approve` - Approve workflow
    - `POST /api/v1/workflows/{id}/reject` - Reject workflow
    
    ### Configuration
    - `GET /api/v1/config` - Get agent configuration
    - `GET /api/v1/capabilities` - Get agent capabilities
    
    ## Error Handling
    
    All endpoints return standardized error responses:
    
    ```json
    {
      "error": "error_type",
      "message": "Human-readable error message",
      "details": [...],
      "timestamp": "2025-01-24T...",
      "path": "/api/v1/endpoint"
    }
    ```
    
    ## Rate Limiting
    
    - 100 requests per minute per IP
    - 1000 requests per hour per IP
    
    ## Authentication
    
    Currently open for development. Production will require:
    - API key authentication
    - JWT tokens
    - Role-based access control
    
    ## Support
    - Documentation: https://docs.optiinfra.com
    - Support: support@optiinfra.com
    - GitHub: https://github.com/optiinfra
    """,
    version="0.1.0",
    contact={
        "name": "OptiInfra Support",
        "email": "support@optiinfra.com",
        "url": "https://optiinfra.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://optiinfra.com/license"
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and readiness endpoints"
        },
        {
            "name": "metrics",
            "description": "Metrics collection and history"
        },
        {
            "name": "analysis",
            "description": "Performance analysis and bottleneck detection"
        },
        {
            "name": "optimization",
            "description": "Optimization recommendations"
        },
        {
            "name": "workflows",
            "description": "Gradual rollout workflows"
        },
        {
            "name": "config",
            "description": "Agent configuration and capabilities"
        }
    ]
)
```

---

## API Endpoint Summary

### Complete API Catalog

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| **Health & Status** ||||
| GET | `/api/v1/health` | Basic health check | ✅ Existing |
| GET | `/api/v1/health/detailed` | Detailed health | ✅ Existing |
| GET | `/api/v1/health/ready` | Readiness probe | ✅ Existing |
| **Metrics** ||||
| POST | `/api/v1/collect/vllm` | Collect vLLM metrics | ✅ Existing |
| POST | `/api/v1/collect/tgi` | Collect TGI metrics | ✅ Existing |
| POST | `/api/v1/collect/sglang` | Collect SGLang metrics | ✅ Existing |
| GET | `/api/v1/history/{instance_id}` | Get metrics history | 🆕 New |
| **Analysis** ||||
| POST | `/api/v1/analyze` | Analyze performance | ✅ Existing |
| **Optimization** ||||
| POST | `/api/v1/optimize` | Generate optimization plan | ✅ Existing |
| **Workflows** ||||
| POST | `/api/v1/workflows` | Start workflow | ✅ Existing |
| GET | `/api/v1/workflows` | List workflows | 🆕 New |
| GET | `/api/v1/workflows/{id}` | Get workflow status | ✅ Existing |
| POST | `/api/v1/workflows/{id}/approve` | Approve workflow | ✅ Existing |
| POST | `/api/v1/workflows/{id}/reject` | Reject workflow | ✅ Existing |
| **Configuration** ||||
| GET | `/api/v1/config` | Get configuration | 🆕 New |
| GET | `/api/v1/capabilities` | Get capabilities | 🆕 New |

**Total**: 17 endpoints (12 existing + 5 new)

---

## Success Criteria

### Functional Requirements
- ✅ All 17 endpoints functional
- ✅ Standardized error responses
- ✅ Request validation
- ✅ Comprehensive OpenAPI documentation
- ✅ Proper HTTP status codes

### Non-Functional Requirements
- ✅ Response time < 1 second (except workflows)
- ✅ Type hints throughout
- ✅ Comprehensive docstrings
- ✅ Tests pass with >80% coverage

---

## Dependencies

### From Previous Phases
- **PHASE2-2.7**: Workflow endpoints
- **PHASE2-2.6**: Optimization endpoints
- **PHASE2-2.5**: Analysis endpoints
- **PHASE2-2.4**: SGLang collector
- **PHASE2-2.3**: TGI collector
- **PHASE2-2.2**: vLLM collector

---

## Next Phase

**PHASE2-2.9**: Integration Testing - Complete end-to-end testing

---

**Status**: Ready for implementation  
**Estimated Completion**: 35 minutes  
**Dependencies**: All previous PHASE2 phases
