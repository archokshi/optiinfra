# PHASE1-1.12 PART2: API Endpoints & Integration - Execution and Validation

**Phase:** Cost Agent - Week 2  
**Objective:** Execute and validate all API endpoints implementation  
**Priority:** HIGH  
**Estimated Effort:** 1.5 hours  
**Date:** October 23, 2025

---

## 📋 OVERVIEW

This document guides you through **executing and validating** the PHASE1-1.12 API Endpoints implementation. You will:

1. **Implement Authentication** - API keys and JWT tokens
2. **Add Rate Limiting** - Protect against abuse
3. **Create Missing Endpoints** - Bulk operations, webhooks, notifications
4. **Test All Endpoints** - Comprehensive API testing
5. **Validate Documentation** - OpenAPI/Swagger specs
6. **Performance Testing** - Load and stress testing

### Success Criteria
- ✅ All 65 endpoints functional
- ✅ Authentication working on all protected endpoints
- ✅ Rate limiting operational
- ✅ 95%+ test coverage
- ✅ < 100ms average response time
- ✅ OpenAPI documentation complete

---

## 🎯 VALIDATION CHECKLIST

### Core Functionality
- [ ] Authentication system working
- [ ] Rate limiting functional
- [ ] All endpoints respond correctly
- [ ] Request validation working
- [ ] Error handling comprehensive

### Testing
- [ ] Unit tests pass (95%+ coverage)
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Load tests pass (1000 req/min)

### Documentation
- [ ] OpenAPI spec complete
- [ ] Swagger UI functional
- [ ] ReDoc functional
- [ ] All endpoints documented

---

## 🚀 STEP 1: IMPLEMENT AUTHENTICATION

### 1.1 Create Database Models

**File:** `src/models/database.py` (add to existing)

```python
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from src.database import Base

class APIKey(Base):
    """API Key model."""
    __tablename__ = "api_keys"
    
    id = Column(String, primary_key=True)
    customer_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime)
    requests_count = Column(Integer, default=0)
```

### 1.2 Create Migration

```bash
# Create migration
cd services/cost-agent
alembic revision -m "add_api_keys_table"
```

**Edit the migration file:**

```python
def upgrade():
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('key_hash', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime()),
        sa.Column('requests_count', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index('ix_api_keys_customer_id', 'api_keys', ['customer_id'])

def downgrade():
    op.drop_index('ix_api_keys_customer_id')
    op.drop_table('api_keys')
```

```bash
# Run migration
alembic upgrade head
```

### 1.3 Implement API Key Manager

Create `src/auth/api_key.py` as specified in PART1.

### 1.4 Implement JWT Handler

**File:** `src/auth/jwt_handler.py`

```python
"""JWT Token Handler."""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


class JWTHandler:
    """Handle JWT token operations."""
    
    @staticmethod
    def create_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Decode and validate JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
```

### 1.5 Create Auth Routes

**File:** `src/api/auth_routes.py`

```python
"""Authentication API Routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db
from src.auth.api_key import APIKeyManager
from src.auth.jwt_handler import JWTHandler
from src.models.requests import CreateAPIKeyRequest, CreateTokenRequest
from src.models.responses import APIKeyResponse, TokenResponse

router = APIRouter(prefix="/auth")


@router.post("/api-key/create", response_model=APIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new API key.
    
    - **customer_id**: Customer ID
    - **name**: Key name/description
    - **expires_days**: Days until expiration (default 365)
    """
    plain_key, key_record = await APIKeyManager.create_key(
        customer_id=request.customer_id,
        name=request.name,
        expires_days=request.expires_days or 365,
        db=db
    )
    
    return APIKeyResponse(
        id=key_record.id,
        key=plain_key,  # Only shown once
        customer_id=key_record.customer_id,
        name=key_record.name,
        created_at=key_record.created_at,
        expires_at=key_record.expires_at
    )


@router.get("/api-key/list", response_model=List[APIKeyResponse])
async def list_api_keys(
    customer_id: str,
    db: Session = Depends(get_db)
):
    """List all API keys for a customer."""
    # Implementation
    pass


@router.delete("/api-key/{key_id}")
async def delete_api_key(
    key_id: str,
    db: Session = Depends(get_db)
):
    """Delete an API key."""
    # Implementation
    pass


@router.post("/token", response_model=TokenResponse)
async def create_token(
    request: CreateTokenRequest
):
    """
    Create JWT token.
    
    - **username**: Username
    - **password**: Password
    """
    # Validate credentials (implement your logic)
    # For now, simple example
    
    token = JWTHandler.create_token(
        data={"sub": request.username, "customer_id": "cust-123"}
    )
    
    return TokenResponse(
        access_token=token,
        token_type="bearer"
    )
```

### 1.6 Test Authentication

```bash
# Test API key creation
curl -X POST http://localhost:8001/api/v1/auth/api-key/create \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "cust-123",
    "name": "Test Key",
    "expires_days": 365
  }'

# Expected response:
# {
#   "id": "key-xxx",
#   "key": "sk_xxxxxxxxxxxxx",
#   "customer_id": "cust-123",
#   "name": "Test Key",
#   "created_at": "2025-10-23T10:00:00",
#   "expires_at": "2026-10-23T10:00:00"
# }

# Test protected endpoint with API key
curl -X GET http://localhost:8001/api/v1/costs/aws \
  -H "X-API-Key: sk_xxxxxxxxxxxxx"
```

---

## 🚀 STEP 2: IMPLEMENT RATE LIMITING

### 2.1 Install Redis

```bash
# Using Docker
docker run -d -p 6379:6379 redis:latest

# Or install locally (Windows)
# Download from: https://github.com/microsoftarchive/redis/releases
```

### 2.2 Create Rate Limiting Middleware

Create `src/middleware/rate_limit.py` as specified in PART1.

### 2.3 Add Middleware to FastAPI

**File:** `src/main.py` (add)

```python
from src.middleware.rate_limit import rate_limiter
from fastapi import Request

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    # Extract customer ID from API key or JWT
    customer_id = request.state.customer_id if hasattr(request.state, 'customer_id') else "anonymous"
    endpoint = request.url.path
    
    # Check rate limit
    await rate_limiter.check_rate_limit(customer_id, endpoint)
    
    response = await call_next(request)
    return response
```

### 2.4 Test Rate Limiting

```bash
# Test rate limiting
for i in {1..70}; do
  curl -X GET http://localhost:8001/api/v1/health \
    -H "X-API-Key: sk_xxxxxxxxxxxxx"
  echo "Request $i"
done

# Expected: First 60 succeed, then 429 errors
```

---

## 🚀 STEP 3: CREATE MISSING ENDPOINTS

### 3.1 Bulk Operations

Create `src/api/bulk_routes.py` as specified in PART1.

### 3.2 Webhooks

**File:** `src/api/webhook_routes.py`

```python
"""Webhook API Routes."""

from fastapi import APIRouter, Depends
from typing import List

from src.auth.dependencies import get_api_key
from src.models.requests import RegisterWebhookRequest
from src.models.responses import WebhookResponse

router = APIRouter(prefix="/webhooks")


@router.post("/register", response_model=WebhookResponse)
async def register_webhook(
    request: RegisterWebhookRequest,
    api_key = Depends(get_api_key)
):
    """
    Register a webhook endpoint.
    
    - **url**: Webhook URL
    - **events**: List of events to subscribe to
    - **secret**: Optional webhook secret for verification
    """
    # Implementation
    pass


@router.get("/list", response_model=List[WebhookResponse])
async def list_webhooks(
    api_key = Depends(get_api_key)
):
    """List all registered webhooks."""
    # Implementation
    pass


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: str,
    request: RegisterWebhookRequest,
    api_key = Depends(get_api_key)
):
    """Update a webhook."""
    # Implementation
    pass


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    api_key = Depends(get_api_key)
):
    """Delete a webhook."""
    # Implementation
    pass
```

### 3.3 Notifications

**File:** `src/api/notification_routes.py`

```python
"""Notification API Routes."""

from fastapi import APIRouter, Depends
from typing import List

from src.auth.dependencies import get_api_key
from src.models.responses import NotificationResponse

router = APIRouter(prefix="/notifications")


@router.get("/list", response_model=List[NotificationResponse])
async def list_notifications(
    customer_id: str,
    unread_only: bool = False,
    limit: int = 50,
    api_key = Depends(get_api_key)
):
    """
    List notifications for a customer.
    
    - **customer_id**: Customer ID
    - **unread_only**: Only return unread notifications
    - **limit**: Maximum number to return
    """
    # Implementation
    pass


@router.post("/mark-read")
async def mark_notifications_read(
    notification_ids: List[str],
    api_key = Depends(get_api_key)
):
    """Mark notifications as read."""
    # Implementation
    pass


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    api_key = Depends(get_api_key)
):
    """Delete a notification."""
    # Implementation
    pass
```

---

## 🚀 STEP 4: COMPREHENSIVE API TESTING

### 4.1 Create Test Structure

```bash
mkdir -p tests/api
touch tests/api/__init__.py
touch tests/api/test_auth.py
touch tests/api/test_costs.py
touch tests/api/test_analysis.py
touch tests/api/test_recommendations.py
touch tests/api/test_execution.py
touch tests/api/test_learning.py
touch tests/api/test_bulk.py
touch tests/api/test_webhooks.py
```

### 4.2 Authentication Tests

**File:** `tests/api/test_auth.py`

```python
"""Test authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_create_api_key():
    """Test API key creation."""
    response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-test",
            "name": "Test Key",
            "expires_days": 365
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["key"].startswith("sk_")
    assert data["customer_id"] == "cust-test"


def test_list_api_keys():
    """Test listing API keys."""
    response = client.get("/api/v1/auth/api-key/list?customer_id=cust-test")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_create_jwt_token():
    """Test JWT token creation."""
    response = client.post(
        "/api/v1/auth/token",
        json={
            "username": "testuser",
            "password": "testpass"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_protected_endpoint_without_auth():
    """Test accessing protected endpoint without auth."""
    response = client.get("/api/v1/costs/aws")
    
    assert response.status_code == 401


def test_protected_endpoint_with_invalid_key():
    """Test accessing protected endpoint with invalid key."""
    response = client.get(
        "/api/v1/costs/aws",
        headers={"X-API-Key": "invalid-key"}
    )
    
    assert response.status_code == 401
```

### 4.3 Rate Limiting Tests

**File:** `tests/api/test_rate_limiting.py`

```python
"""Test rate limiting."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_rate_limit_per_minute():
    """Test per-minute rate limit."""
    # Create API key
    response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-rate-test",
            "name": "Rate Test Key",
            "expires_days": 1
        }
    )
    api_key = response.json()["key"]
    
    # Make 61 requests
    success_count = 0
    rate_limited_count = 0
    
    for i in range(61):
        response = client.get(
            "/api/v1/health",
            headers={"X-API-Key": api_key}
        )
        
        if response.status_code == 200:
            success_count += 1
        elif response.status_code == 429:
            rate_limited_count += 1
    
    # Should have 60 successes and 1 rate limited
    assert success_count == 60
    assert rate_limited_count == 1
```

### 4.4 Endpoint Tests

**File:** `tests/api/test_costs.py`

```python
"""Test cost endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


@pytest.fixture
def api_key():
    """Create API key for tests."""
    response = client.post(
        "/api/v1/auth/api-key/create",
        json={
            "customer_id": "cust-test",
            "name": "Test Key",
            "expires_days": 1
        }
    )
    return response.json()["key"]


def test_get_aws_costs(api_key):
    """Test getting AWS costs."""
    response = client.get(
        "/api/v1/costs/aws",
        headers={"X-API-Key": api_key},
        params={
            "customer_id": "cust-test",
            "start_date": "2025-10-01",
            "end_date": "2025-10-23"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_cost" in data
    assert "breakdown" in data


def test_get_multi_cloud_costs(api_key):
    """Test getting multi-cloud costs."""
    response = client.get(
        "/api/v1/costs/multi-cloud",
        headers={"X-API-Key": api_key},
        params={
            "customer_id": "cust-test",
            "start_date": "2025-10-01",
            "end_date": "2025-10-23"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "aws" in data
    assert "gcp" in data
    assert "azure" in data


def test_export_costs(api_key):
    """Test exporting costs."""
    response = client.get(
        "/api/v1/costs/export",
        headers={"X-API-Key": api_key},
        params={
            "customer_id": "cust-test",
            "format": "csv"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv"
```

### 4.5 Run All Tests

```bash
# Run all API tests
python -m pytest tests/api/ -v

# Run with coverage
python -m pytest tests/api/ --cov=src.api --cov-report=html

# Run specific test file
python -m pytest tests/api/test_auth.py -v
```

---

## 🚀 STEP 5: VALIDATE DOCUMENTATION

### 5.1 Access Swagger UI

```bash
# Start the server
python -m src.main

# Open browser
# http://localhost:8001/docs
```

**Verify:**
- ✅ All 65 endpoints listed
- ✅ Authentication schemes shown
- ✅ Request/response examples present
- ✅ Try-it-out functionality works

### 5.2 Access ReDoc

```bash
# Open browser
# http://localhost:8001/redoc
```

**Verify:**
- ✅ Clean documentation layout
- ✅ All endpoints organized by tags
- ✅ Examples visible
- ✅ Search functionality works

### 5.3 Export OpenAPI Spec

```bash
# Export OpenAPI spec
curl http://localhost:8001/openapi.json > openapi.json

# Validate spec
npx @apidevtools/swagger-cli validate openapi.json
```

---

## 🚀 STEP 6: PERFORMANCE TESTING

### 6.1 Install Load Testing Tools

```bash
pip install locust
```

### 6.2 Create Load Test

**File:** `tests/load/locustfile.py`

```python
"""Load testing with Locust."""

from locust import HttpUser, task, between


class CostAgentUser(HttpUser):
    """Simulate Cost Agent API user."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Create API key on start."""
        response = self.client.post(
            "/api/v1/auth/api-key/create",
            json={
                "customer_id": "cust-load-test",
                "name": "Load Test Key",
                "expires_days": 1
            }
        )
        self.api_key = response.json()["key"]
    
    @task(3)
    def get_health(self):
        """Test health endpoint."""
        self.client.get(
            "/api/v1/health",
            headers={"X-API-Key": self.api_key}
        )
    
    @task(2)
    def get_costs(self):
        """Test costs endpoint."""
        self.client.get(
            "/api/v1/costs/aws",
            headers={"X-API-Key": self.api_key},
            params={
                "customer_id": "cust-load-test",
                "start_date": "2025-10-01",
                "end_date": "2025-10-23"
            }
        )
    
    @task(1)
    def generate_recommendations(self):
        """Test recommendations endpoint."""
        self.client.post(
            "/api/v1/recommendations/generate",
            headers={"X-API-Key": self.api_key},
            json={
                "customer_id": "cust-load-test",
                "lookback_days": 30
            }
        )
```

### 6.3 Run Load Test

```bash
# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8001

# Open browser: http://localhost:8089
# Set users: 100
# Spawn rate: 10
# Run test for 5 minutes
```

**Performance Targets:**
- ✅ < 100ms average response time
- ✅ < 500ms 95th percentile
- ✅ < 1% error rate
- ✅ Handle 1000 req/min per customer

---

## ✅ VALIDATION CHECKLIST

### Authentication & Security
- [ ] API key creation works
- [ ] API key validation works
- [ ] JWT token creation works
- [ ] JWT token validation works
- [ ] Protected endpoints require auth
- [ ] Invalid keys rejected
- [ ] Expired keys rejected

### Rate Limiting
- [ ] Per-minute limit enforced
- [ ] Per-hour limit enforced
- [ ] 429 status code returned
- [ ] Rate limit headers present
- [ ] Redis connection working

### Endpoints
- [ ] All 65 endpoints implemented
- [ ] All endpoints respond correctly
- [ ] Request validation working
- [ ] Error handling comprehensive
- [ ] Response format consistent

### Testing
- [ ] Unit tests pass (95%+ coverage)
- [ ] Integration tests pass
- [ ] Security tests pass
- [ ] Load tests pass
- [ ] No critical bugs

### Documentation
- [ ] OpenAPI spec complete
- [ ] Swagger UI functional
- [ ] ReDoc functional
- [ ] All endpoints documented
- [ ] Examples present

### Performance
- [ ] < 100ms average response time
- [ ] < 500ms 95th percentile
- [ ] Handle 1000 req/min
- [ ] No memory leaks
- [ ] Efficient database queries

---

## 🎯 SUCCESS METRICS

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Endpoints implemented | 65 | ___ | ⬜ |
| Test coverage | 95% | ___% | ⬜ |
| Tests passing | 100% | ___% | ⬜ |
| Avg response time | < 100ms | ___ms | ⬜ |
| 95th percentile | < 500ms | ___ms | ⬜ |
| Requests per minute | 1000 | ___ | ⬜ |
| Error rate | < 1% | ___% | ⬜ |
| Documentation coverage | 100% | ___% | ⬜ |

---

## 🐛 TROUBLESHOOTING

### Issue 1: Redis Connection Failed
```
Error: Connection refused to Redis
```

**Solution:**
```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Or check if Redis is running
redis-cli ping
```

### Issue 2: Rate Limiting Not Working
```
Warning: Rate limiting bypassed
```

**Solution:**
- Check Redis connection
- Verify middleware is registered
- Check customer ID extraction

### Issue 3: Authentication Fails
```
Error: 401 Unauthorized
```

**Solution:**
- Verify API key is correct
- Check key hasn't expired
- Ensure header name is correct (`X-API-Key`)

### Issue 4: Tests Failing
```
FAILED tests/api/test_auth.py::test_create_api_key
```

**Solution:**
```bash
# Check database connection
# Run migrations
alembic upgrade head

# Clear test database
python scripts/clear_test_db.py
```

---

## 📊 FINAL VALIDATION

### Run Complete Test Suite

```bash
# 1. Run all tests
python -m pytest tests/ -v --cov=src --cov-report=html

# 2. Check coverage
open htmlcov/index.html

# 3. Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8001

# 4. Validate OpenAPI spec
curl http://localhost:8001/openapi.json | jq '.' > openapi.json
npx @apidevtools/swagger-cli validate openapi.json

# 5. Test authentication
curl -X POST http://localhost:8001/api/v1/auth/api-key/create \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"cust-test","name":"Test","expires_days":365}'

# 6. Test rate limiting
for i in {1..70}; do curl -H "X-API-Key: sk_xxx" http://localhost:8001/api/v1/health; done
```

---

## 🎉 COMPLETION CRITERIA

**PHASE1-1.12 is complete when:**

### Code
- ✅ All 65 endpoints implemented
- ✅ Authentication system working
- ✅ Rate limiting functional
- ✅ Request validation comprehensive
- ✅ Error handling robust

### Testing
- ✅ 95%+ test coverage
- ✅ All tests passing
- ✅ Load tests successful
- ✅ Security tests passed

### Documentation
- ✅ OpenAPI spec complete
- ✅ Swagger UI functional
- ✅ ReDoc functional
- ✅ All endpoints documented

### Performance
- ✅ < 100ms average response time
- ✅ Handle 1000 req/min
- ✅ < 1% error rate
- ✅ No memory leaks

---

## 📝 NEXT STEPS

After completing PHASE1-1.12:

1. **Deploy to Staging** - Test in staging environment
2. **Security Audit** - Penetration testing
3. **Performance Tuning** - Optimize slow endpoints
4. **User Acceptance Testing** - Gather feedback
5. **Production Deployment** - Deploy to production

---

**END OF PART2**
