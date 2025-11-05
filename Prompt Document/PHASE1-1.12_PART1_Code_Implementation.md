# PHASE1-1.12 PART1: API Endpoints & Integration - Code Implementation

**Phase:** Cost Agent - Week 2  
**Objective:** Consolidate and enhance all API endpoints with comprehensive documentation and testing  
**Priority:** HIGH  
**Estimated Effort:** 1.5-2 hours  
**Date:** October 23, 2025

---

## 📋 OVERVIEW

PHASE1-1.12 focuses on **consolidating, documenting, and enhancing all Cost Agent API endpoints**. After implementing all core components (Data Collection, Analysis, LLM Integration, Recommendations, Execution, and Learning Loop), we now need to:

1. **Consolidate Endpoints** - Organize all API routes systematically
2. **Add Missing Endpoints** - Fill gaps in functionality
3. **Enhance Documentation** - OpenAPI/Swagger specs
4. **Add Authentication** - API key and JWT support
5. **Implement Rate Limiting** - Protect against abuse
6. **Add Request Validation** - Comprehensive input validation
7. **Create API Tests** - Test all endpoints thoroughly

**Key Differences from Previous Phases:**
- **PHASE1-1.1-1.6:** Built data collection endpoints
- **PHASE1-1.7:** Built analysis endpoints
- **PHASE1-1.8:** Built LLM integration endpoints
- **PHASE1-1.9:** Built recommendation endpoints
- **PHASE1-1.10:** Built execution endpoints
- **PHASE1-1.11:** Built learning loop endpoints
- **PHASE1-1.12:** **Consolidates ALL endpoints with auth, docs, and testing**

**Expected Impact:** Production-ready API with 100% endpoint coverage and comprehensive documentation

---

## 🎯 OBJECTIVES

### Primary Goals
1. **API Consolidation:**
   - Audit all existing endpoints
   - Organize by functional area
   - Ensure consistent naming
   - Add missing endpoints

2. **Authentication & Security:**
   - API key authentication
   - JWT token support
   - Role-based access control (RBAC)
   - Rate limiting per customer

3. **Documentation:**
   - OpenAPI 3.0 specifications
   - Interactive Swagger UI
   - ReDoc documentation
   - Example requests/responses

4. **Request Validation:**
   - Pydantic models for all requests
   - Input sanitization
   - Error messages with details
   - Field-level validation

5. **API Testing:**
   - Unit tests for all endpoints
   - Integration tests
   - Load testing
   - Security testing

### Success Criteria
- ✅ 50+ API endpoints documented
- ✅ 100% endpoints have authentication
- ✅ OpenAPI spec complete
- ✅ 95%+ test coverage for API layer
- ✅ Rate limiting implemented
- ✅ < 100ms average response time

---

## 🏗️ ARCHITECTURE

### API Organization

```
Cost Agent API Structure:
├── /api/v1/
│   ├── /health              # Health & Status
│   ├── /auth                # Authentication
│   ├── /customers           # Customer Management
│   ├── /costs               # Cost Data
│   │   ├── /aws
│   │   ├── /gcp
│   │   ├── /azure
│   │   └── /multi-cloud
│   ├── /analysis            # Cost Analysis
│   │   ├── /anomalies
│   │   ├── /trends
│   │   └── /forecasts
│   ├── /recommendations     # Recommendations
│   │   ├── /generate
│   │   ├── /list
│   │   ├── /detail
│   │   └── /approve
│   ├── /execution           # Execution
│   │   ├── /execute
│   │   ├── /status
│   │   ├── /history
│   │   └── /rollback
│   ├── /learning            # Learning Loop
│   │   ├── /track-outcome
│   │   ├── /metrics
│   │   ├── /insights
│   │   └── /similar-cases
│   └── /admin               # Admin Functions
│       ├── /metrics
│       ├── /logs
│       └── /config
```

---

## 📦 IMPLEMENTATION PHASES

### Phase 1: API Audit & Consolidation (20 min)

**Objective:** Audit existing endpoints and create consolidated router

**Tasks:**
1. List all existing endpoints
2. Identify gaps and missing functionality
3. Create unified API structure
4. Consolidate route files

**Files to Create/Modify:**
- `src/api/__init__.py` - Export all routers
- `src/api/v1/__init__.py` - V1 API router
- `src/main.py` - Update to use consolidated routers

---

### Phase 2: Authentication & Security (25 min)

**Objective:** Implement API authentication and security

**Components:**
1. **API Key Authentication**
   - Generate and validate API keys
   - Store in database
   - Per-customer keys

2. **JWT Token Support**
   - Token generation
   - Token validation
   - Refresh tokens

3. **Rate Limiting**
   - Per-customer limits
   - Per-endpoint limits
   - Redis-based tracking

**Files to Create:**
- `src/auth/api_key.py` - API key management
- `src/auth/jwt_handler.py` - JWT token handling
- `src/auth/dependencies.py` - FastAPI dependencies
- `src/middleware/rate_limit.py` - Rate limiting middleware
- `src/models/auth.py` - Auth Pydantic models

---

### Phase 3: Enhanced Documentation (20 min)

**Objective:** Create comprehensive API documentation

**Components:**
1. **OpenAPI Specifications**
   - Complete endpoint descriptions
   - Request/response examples
   - Error code documentation
   - Authentication requirements

2. **Interactive Documentation**
   - Swagger UI customization
   - ReDoc styling
   - Try-it-out examples

**Files to Modify:**
- `src/main.py` - Enhanced OpenAPI config
- All route files - Add detailed docstrings
- `docs/API.md` - API documentation

---

### Phase 4: Request Validation Enhancement (15 min)

**Objective:** Enhance request validation across all endpoints

**Components:**
1. **Pydantic Models**
   - Request models for all endpoints
   - Response models
   - Error models

2. **Custom Validators**
   - Date range validation
   - Resource ID validation
   - Cost threshold validation

**Files to Create/Modify:**
- `src/models/requests.py` - Request models
- `src/models/responses.py` - Response models
- `src/validators/` - Custom validators

---

### Phase 5: Missing Endpoints (20 min)

**Objective:** Add missing functionality endpoints

**New Endpoints:**
1. **Bulk Operations**
   - `POST /api/v1/recommendations/bulk-generate`
   - `POST /api/v1/execution/bulk-execute`

2. **Export/Import**
   - `GET /api/v1/costs/export`
   - `POST /api/v1/recommendations/import`

3. **Webhooks**
   - `POST /api/v1/webhooks/register`
   - `GET /api/v1/webhooks/list`
   - `DELETE /api/v1/webhooks/{id}`

4. **Notifications**
   - `GET /api/v1/notifications/list`
   - `POST /api/v1/notifications/mark-read`

**Files to Create:**
- `src/api/bulk_routes.py` - Bulk operations
- `src/api/webhook_routes.py` - Webhook management
- `src/api/notification_routes.py` - Notifications

---

### Phase 6: API Testing (20 min)

**Objective:** Comprehensive API endpoint testing

**Test Categories:**
1. **Unit Tests** - Each endpoint individually
2. **Integration Tests** - End-to-end flows
3. **Security Tests** - Auth and rate limiting
4. **Load Tests** - Performance under load

**Files to Create:**
- `tests/api/test_health.py`
- `tests/api/test_auth.py`
- `tests/api/test_costs.py`
- `tests/api/test_analysis.py`
- `tests/api/test_recommendations.py`
- `tests/api/test_execution.py`
- `tests/api/test_learning.py`
- `tests/api/test_bulk.py`
- `tests/api/test_webhooks.py`

---

## 📋 DETAILED IMPLEMENTATION

### Phase 1: API Audit & Consolidation

#### Step 1.1: Audit Existing Endpoints

**Current Endpoints (from previous phases):**

**Health & Status:**
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/detailed` - Detailed health

**Cost Collection:**
- `GET /api/v1/aws/costs` - AWS costs
- `GET /api/v1/gcp/costs` - GCP costs
- `GET /api/v1/azure/costs` - Azure costs

**Analysis:**
- `POST /api/v1/analysis/analyze` - Analyze costs
- `GET /api/v1/analysis/anomalies` - Get anomalies
- `GET /api/v1/analysis/trends` - Get trends

**Recommendations:**
- `POST /api/v1/recommendations/generate` - Generate
- `GET /api/v1/recommendations/{customer_id}` - List
- `GET /api/v1/recommendations/detail/{id}` - Details
- `POST /api/v1/recommendations/{id}/approve` - Approve
- `POST /api/v1/recommendations/{id}/reject` - Reject

**Execution:**
- `POST /api/v1/execution/execute` - Execute
- `GET /api/v1/execution/status/{id}` - Status
- `GET /api/v1/execution/history` - History
- `POST /api/v1/execution/rollback/{id}` - Rollback

**Learning Loop:**
- `POST /api/v1/learning/track-outcome` - Track outcome
- `GET /api/v1/learning/metrics` - Metrics
- `GET /api/v1/learning/insights` - Insights
- `GET /api/v1/learning/similar-cases/{id}` - Similar cases

**Total Existing:** ~30 endpoints

#### Step 1.2: Create Consolidated Router

**File:** `src/api/v1/__init__.py`

```python
"""
API v1 Router.

Consolidates all v1 endpoints.
"""

from fastapi import APIRouter
from src.api import (
    health,
    auth_routes,
    cost_routes,
    analysis_routes,
    recommendation_routes,
    execution_routes,
    learning_routes,
    bulk_routes,
    webhook_routes,
    notification_routes
)

# Create v1 router
router = APIRouter(prefix="/api/v1")

# Include all sub-routers
router.include_router(health.router, tags=["health"])
router.include_router(auth_routes.router, tags=["auth"])
router.include_router(cost_routes.router, tags=["costs"])
router.include_router(analysis_routes.router, tags=["analysis"])
router.include_router(recommendation_routes.router, tags=["recommendations"])
router.include_router(execution_routes.router, tags=["execution"])
router.include_router(learning_routes.router, tags=["learning"])
router.include_router(bulk_routes.router, tags=["bulk"])
router.include_router(webhook_routes.router, tags=["webhooks"])
router.include_router(notification_routes.router, tags=["notifications"])
```

---

### Phase 2: Authentication & Security

#### Step 2.1: API Key Authentication

**File:** `src/auth/api_key.py`

```python
"""
API Key Authentication.

Manages API key generation, validation, and storage.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from src.database import get_db
from src.models.database import APIKey


class APIKeyManager:
    """Manages API keys."""
    
    @staticmethod
    def generate_key(prefix: str = "sk") -> str:
        """Generate a new API key."""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    @staticmethod
    def hash_key(api_key: str) -> str:
        """Hash an API key for storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    @staticmethod
    async def create_key(
        customer_id: str,
        name: str,
        expires_days: int = 365,
        db: Session = None
    ) -> tuple[str, APIKey]:
        """
        Create a new API key.
        
        Returns:
            Tuple of (plain_key, db_record)
        """
        # Generate key
        plain_key = APIKeyManager.generate_key()
        hashed_key = APIKeyManager.hash_key(plain_key)
        
        # Create database record
        api_key = APIKey(
            customer_id=customer_id,
            name=name,
            key_hash=hashed_key,
            expires_at=datetime.utcnow() + timedelta(days=expires_days),
            created_at=datetime.utcnow()
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        return plain_key, api_key
    
    @staticmethod
    async def validate_key(
        api_key: str,
        db: Session
    ) -> Optional[APIKey]:
        """
        Validate an API key.
        
        Returns:
            APIKey record if valid, None otherwise
        """
        hashed_key = APIKeyManager.hash_key(api_key)
        
        # Query database
        key_record = db.query(APIKey).filter(
            APIKey.key_hash == hashed_key,
            APIKey.is_active == True,
            APIKey.expires_at > datetime.utcnow()
        ).first()
        
        if key_record:
            # Update last used
            key_record.last_used_at = datetime.utcnow()
            db.commit()
        
        return key_record
```

#### Step 2.2: FastAPI Dependencies

**File:** `src/auth/dependencies.py`

```python
"""
Authentication Dependencies.

FastAPI dependencies for authentication.
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, HTTPBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.auth.api_key import APIKeyManager
from src.auth.jwt_handler import JWTHandler

# Security schemes
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: Session = Depends(get_db)
):
    """Validate API key."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    key_record = await APIKeyManager.validate_key(api_key, db)
    
    if not key_record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return key_record


async def get_current_user(
    token: str = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    """Validate JWT token."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = JWTHandler.decode_token(token.credentials)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload
```

#### Step 2.3: Rate Limiting

**File:** `src/middleware/rate_limit.py`

```python
"""
Rate Limiting Middleware.

Implements rate limiting per customer and endpoint.
"""

import time
from fastapi import Request, HTTPException
from redis import Redis
from typing import Optional

redis_client = Redis(host='localhost', port=6379, decode_responses=True)


class RateLimiter:
    """Rate limiter using Redis."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    async def check_rate_limit(
        self,
        customer_id: str,
        endpoint: str
    ) -> bool:
        """
        Check if request is within rate limit.
        
        Returns:
            True if allowed, raises HTTPException if exceeded
        """
        current_time = int(time.time())
        
        # Check per-minute limit
        minute_key = f"rate_limit:{customer_id}:{endpoint}:minute:{current_time // 60}"
        minute_count = redis_client.incr(minute_key)
        redis_client.expire(minute_key, 60)
        
        if minute_count > self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
            )
        
        # Check per-hour limit
        hour_key = f"rate_limit:{customer_id}:{endpoint}:hour:{current_time // 3600}"
        hour_count = redis_client.incr(hour_key)
        redis_client.expire(hour_key, 3600)
        
        if hour_count > self.requests_per_hour:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {self.requests_per_hour} requests per hour"
            )
        
        return True


# Global rate limiter
rate_limiter = RateLimiter()
```

---

### Phase 3: Enhanced Documentation

#### Step 3.1: OpenAPI Configuration

**File:** `src/main.py` (modifications)

```python
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="OptiInfra Cost Agent API",
    description="""
    # OptiInfra Cost Agent API
    
    The Cost Agent API provides comprehensive cost optimization capabilities for cloud infrastructure.
    
    ## Features
    - **Cost Collection**: Collect costs from AWS, GCP, and Azure
    - **Analysis**: Detect anomalies, trends, and forecasts
    - **Recommendations**: Generate intelligent cost-saving recommendations
    - **Execution**: Execute optimizations with approval workflows
    - **Learning**: Continuous learning from execution outcomes
    
    ## Authentication
    All endpoints require authentication via:
    - **API Key**: Include `X-API-Key` header
    - **JWT Token**: Include `Authorization: Bearer <token>` header
    
    ## Rate Limits
    - 60 requests per minute per customer
    - 1000 requests per hour per customer
    
    ## Support
    - Documentation: https://docs.optiinfra.com
    - Support: support@optiinfra.com
    """,
    version="1.0.0",
    contact={
        "name": "OptiInfra Support",
        "email": "support@optiinfra.com",
        "url": "https://optiinfra.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://optiinfra.com/license"
    }
)


def custom_openapi():
    """Custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "APIKey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        },
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
```

---

### Phase 4: Missing Endpoints

#### Step 4.1: Bulk Operations

**File:** `src/api/bulk_routes.py`

```python
"""
Bulk Operations API Routes.

Endpoints for bulk operations on recommendations and executions.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from src.auth.dependencies import get_api_key
from src.models.requests import BulkGenerateRequest, BulkExecuteRequest
from src.models.responses import BulkOperationResponse

router = APIRouter(prefix="/bulk")


@router.post("/recommendations/generate", response_model=BulkOperationResponse)
async def bulk_generate_recommendations(
    request: BulkGenerateRequest,
    api_key = Depends(get_api_key)
):
    """
    Generate recommendations for multiple customers in bulk.
    
    - **customer_ids**: List of customer IDs
    - **filters**: Optional filters to apply
    
    Returns bulk operation status and results.
    """
    # Implementation
    pass


@router.post("/execution/execute", response_model=BulkOperationResponse)
async def bulk_execute_recommendations(
    request: BulkExecuteRequest,
    api_key = Depends(get_api_key)
):
    """
    Execute multiple recommendations in bulk.
    
    - **recommendation_ids**: List of recommendation IDs
    - **execution_options**: Execution configuration
    
    Returns bulk execution status.
    """
    # Implementation
    pass
```

---

## 📊 COMPLETE ENDPOINT LIST

### Health & Status (2 endpoints)
- `GET /api/v1/health`
- `GET /api/v1/health/detailed`

### Authentication (4 endpoints)
- `POST /api/v1/auth/api-key/create`
- `GET /api/v1/auth/api-key/list`
- `DELETE /api/v1/auth/api-key/{id}`
- `POST /api/v1/auth/token`

### Cost Collection (10 endpoints)
- `GET /api/v1/costs/aws`
- `GET /api/v1/costs/gcp`
- `GET /api/v1/costs/azure`
- `GET /api/v1/costs/multi-cloud`
- `GET /api/v1/costs/summary`
- `GET /api/v1/costs/breakdown`
- `GET /api/v1/costs/export`
- `POST /api/v1/costs/refresh`
- `GET /api/v1/costs/history`
- `GET /api/v1/costs/forecast`

### Analysis (8 endpoints)
- `POST /api/v1/analysis/analyze`
- `GET /api/v1/analysis/anomalies`
- `GET /api/v1/analysis/trends`
- `GET /api/v1/analysis/forecasts`
- `GET /api/v1/analysis/insights`
- `GET /api/v1/analysis/summary`
- `POST /api/v1/analysis/custom`
- `GET /api/v1/analysis/export`

### Recommendations (10 endpoints)
- `POST /api/v1/recommendations/generate`
- `GET /api/v1/recommendations/{customer_id}`
- `GET /api/v1/recommendations/detail/{id}`
- `POST /api/v1/recommendations/{id}/approve`
- `POST /api/v1/recommendations/{id}/reject`
- `GET /api/v1/recommendations/pending`
- `GET /api/v1/recommendations/history`
- `POST /api/v1/recommendations/import`
- `GET /api/v1/recommendations/export`
- `GET /api/v1/recommendations/stats`

### Execution (8 endpoints)
- `POST /api/v1/execution/execute`
- `GET /api/v1/execution/status/{id}`
- `GET /api/v1/execution/history`
- `POST /api/v1/execution/rollback/{id}`
- `GET /api/v1/execution/logs/{id}`
- `POST /api/v1/execution/cancel/{id}`
- `GET /api/v1/execution/summary`
- `GET /api/v1/execution/export`

### Learning Loop (12 endpoints)
- `POST /api/v1/learning/track-outcome`
- `GET /api/v1/learning/metrics`
- `GET /api/v1/learning/insights`
- `GET /api/v1/learning/similar-cases/{id}`
- `POST /api/v1/learning/run-cycle`
- `GET /api/v1/learning/accuracy/{type}`
- `GET /api/v1/learning/success-patterns/{type}`
- `GET /api/v1/learning/failure-patterns/{type}`
- `GET /api/v1/learning/opportunities`
- `GET /api/v1/learning/scoring-weights`
- `GET /api/v1/learning/prediction-model/{type}`
- `GET /api/v1/learning/risk-model/{type}`

### Bulk Operations (4 endpoints)
- `POST /api/v1/bulk/recommendations/generate`
- `POST /api/v1/bulk/execution/execute`
- `GET /api/v1/bulk/status/{id}`
- `GET /api/v1/bulk/history`

### Webhooks (4 endpoints)
- `POST /api/v1/webhooks/register`
- `GET /api/v1/webhooks/list`
- `PUT /api/v1/webhooks/{id}`
- `DELETE /api/v1/webhooks/{id}`

### Notifications (3 endpoints)
- `GET /api/v1/notifications/list`
- `POST /api/v1/notifications/mark-read`
- `DELETE /api/v1/notifications/{id}`

**Total: 65 endpoints**

---

## ✅ ACCEPTANCE CRITERIA

### Functional Requirements
- ✅ All 65 endpoints implemented
- ✅ Authentication on all protected endpoints
- ✅ Rate limiting functional
- ✅ OpenAPI documentation complete
- ✅ Request validation on all endpoints
- ✅ Error handling comprehensive

### Non-Functional Requirements
- ✅ < 100ms average response time
- ✅ 95%+ test coverage
- ✅ 99.9% uptime
- ✅ Handle 1000 req/min per customer
- ✅ Secure (HTTPS, auth, rate limiting)

### Documentation Requirements
- ✅ OpenAPI 3.0 spec complete
- ✅ Swagger UI functional
- ✅ ReDoc functional
- ✅ Example requests for all endpoints
- ✅ Error codes documented

---

## 🚀 NEXT STEPS

After completing PHASE1-1.12:

1. **Deploy API** - Production deployment
2. **Monitor Performance** - Track metrics
3. **Gather Feedback** - From users
4. **Iterate** - Based on usage patterns

---

**END OF PART1**
