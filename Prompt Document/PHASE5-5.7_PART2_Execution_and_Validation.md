# PHASE5-5.7 PART2: API Security - Execution and Validation

**Phase**: PHASE5-5.7  
**Component**: Portal & Production - API Security  
**Estimated Time**: 20 minutes  
**Prerequisites**: PHASE5-5.7_PART1 completed, ALL agents running

---

## Prerequisites Check

### Required Tools

```bash
# Check Python
python --version

# Check pytest
pytest --version

# Check curl (for API testing)
curl --version
```

**Expected**: All tools installed and accessible

---

## Execution Steps

### Step 1: Create Shared Middleware Directory

```bash
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Create middleware directory
mkdir shared\middleware
mkdir shared\validation
mkdir shared\config
mkdir shared\tests
```

---

### Step 2: Create All Middleware Files

Create the following files from PART1:

1. ✅ `shared/middleware/__init__.py`
2. ✅ `shared/middleware/rate_limiter.py`
3. ✅ `shared/middleware/request_validator.py`
4. ✅ `shared/middleware/security_headers.py`
5. ✅ `shared/middleware/api_auth.py`
6. ✅ `shared/validation/__init__.py`
7. ✅ `shared/validation/schemas.py`
8. ✅ `shared/config/security.py`
9. ✅ `shared/tests/test_security.py`

---

### Step 3: Update Agent Main Files

Update each agent's `main.py` to include security middleware:

```bash
# Update Cost Agent
# File: services/cost-agent/src/main.py

# Update Performance Agent
# File: services/performance-agent/src/main.py

# Update Resource Agent
# File: services/resource-agent/src/main.py

# Update Application Agent
# File: services/application-agent/src/main.py
```

---

### Step 4: Install Required Dependencies

```bash
# Add to requirements.txt for each agent
cd services\cost-agent
echo "pydantic[email]==2.5.0" >> requirements.txt

# Install dependencies
pip install -r requirements.txt

# Repeat for other agents
```

---

### Step 5: Generate API Keys

```bash
# Run Python script to generate API keys
python -c "
from shared.middleware.api_auth import api_key_manager

# Generate keys for each agent
cost_key = api_key_manager.generate_key()
perf_key = api_key_manager.generate_key()
resource_key = api_key_manager.generate_key()
app_key = api_key_manager.generate_key()
portal_key = api_key_manager.generate_key()

print('Cost Agent API Key:', cost_key)
print('Performance Agent API Key:', perf_key)
print('Resource Agent API Key:', resource_key)
print('Application Agent API Key:', app_key)
print('Portal API Key:', portal_key)
"
```

**Save these keys securely!**

---

### Step 6: Update Environment Variables

Add API keys to `.env` files:

```bash
# services/cost-agent/.env
API_KEY=<cost-agent-key>

# services/performance-agent/.env
API_KEY=<performance-agent-key>

# services/resource-agent/.env
API_KEY=<resource-agent-key>

# services/application-agent/.env
API_KEY=<application-agent-key>

# portal/.env
COST_AGENT_API_KEY=<cost-agent-key>
PERFORMANCE_AGENT_API_KEY=<performance-agent-key>
RESOURCE_AGENT_API_KEY=<resource-agent-key>
APPLICATION_AGENT_API_KEY=<application-agent-key>
```

---

### Step 7: Start Services with Security

```bash
# Start Cost Agent
cd services\cost-agent
uvicorn src.main:app --host 0.0.0.0 --port 8001

# Start Performance Agent (in new terminal)
cd services\performance-agent
uvicorn src.main:app --host 0.0.0.0 --port 8002

# Start Resource Agent (in new terminal)
cd services\resource-agent
uvicorn src.main:app --host 0.0.0.0 --port 8003

# Start Application Agent (in new terminal)
cd services\application-agent
uvicorn src.main:app --host 0.0.0.0 --port 8004
```

---

## Validation Steps

### Test 1: Verify Security Headers

```bash
# Test Cost Agent
curl -I http://localhost:8001/health

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Content-Security-Policy: ...
```

**✅ Pass Criteria**: All security headers present

---

### Test 2: Test Rate Limiting

```bash
# Send multiple requests quickly
for i in {1..70}; do
  curl -X GET http://localhost:8001/health \
    -H "X-API-Key: <your-api-key>" \
    -w "\nStatus: %{http_code}\n"
done

# Expected: First 60 succeed (200), then 429 (Too Many Requests)
```

**✅ Pass Criteria**: Rate limiting kicks in after 60 requests

---

### Test 3: Test API Key Authentication

```bash
# Test without API key (should fail)
curl -X GET http://localhost:8001/api/analyze \
  -H "Content-Type: application/json"

# Expected: 401 Unauthorized

# Test with valid API key (should succeed)
curl -X GET http://localhost:8001/health \
  -H "X-API-Key: <your-api-key>"

# Expected: 200 OK
```

**✅ Pass Criteria**: Requests without API key are rejected

---

### Test 4: Test SQL Injection Prevention

```bash
# Try SQL injection in query parameter
curl -X GET "http://localhost:8001/api/analyze?query='; DROP TABLE users; --" \
  -H "X-API-Key: <your-api-key>"

# Expected: 400 Bad Request with error message
```

**✅ Pass Criteria**: SQL injection attempts are blocked

---

### Test 5: Test XSS Prevention

```bash
# Try XSS in request body
curl -X POST http://localhost:8001/api/analyze \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "context": "<script>alert(\"xss\")</script>"
  }'

# Expected: 400 Bad Request
```

**✅ Pass Criteria**: XSS attempts are blocked

---

### Test 6: Test Path Traversal Prevention

```bash
# Try path traversal
curl -X GET "http://localhost:8001/api/files/../../etc/passwd" \
  -H "X-API-Key: <your-api-key>"

# Expected: 400 Bad Request
```

**✅ Pass Criteria**: Path traversal attempts are blocked

---

### Test 7: Test Request Size Limits

```bash
# Create large payload (>10MB)
python -c "
import requests
import json

# Create 11MB payload
large_data = {'data': 'x' * (11 * 1024 * 1024)}

response = requests.post(
    'http://localhost:8001/api/analyze',
    headers={'X-API-Key': '<your-api-key>'},
    json=large_data
)

print(f'Status: {response.status_code}')
print(f'Response: {response.text}')
"

# Expected: 400 Bad Request (payload too large)
```

**✅ Pass Criteria**: Large requests are rejected

---

### Test 8: Test Input Validation with Pydantic

```bash
# Test invalid cloud provider
curl -X POST http://localhost:8001/api/analyze \
  -H "X-API-Key: <your-api-key>" \
  -H "Content-Type: application/json" \
  -d '{
    "cloud_provider": "invalid_provider",
    "time_range": "24h"
  }'

# Expected: 422 Unprocessable Entity (validation error)
```

**✅ Pass Criteria**: Invalid input is rejected with validation error

---

### Test 9: Run Security Tests

```bash
# Run security test suite
cd shared
pytest tests/test_security.py -v

# Expected: All tests pass
```

**✅ Pass Criteria**: All security tests pass

---

### Test 10: Test CORS Configuration

```bash
# Test CORS preflight
curl -X OPTIONS http://localhost:8001/api/analyze \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected headers:
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE
```

**✅ Pass Criteria**: CORS headers configured correctly

---

## Troubleshooting

### Issue: Rate limiting not working

**Check**:
```bash
# Verify middleware is loaded
curl -v http://localhost:8001/health

# Check logs for rate limit messages
```

**Common Causes**:
- Middleware not added to app
- Middleware order incorrect
- Rate limiter not initialized

---

### Issue: API key authentication failing

**Check**:
```bash
# Verify API key is correct
echo $API_KEY

# Check if key is in manager
python -c "
from shared.middleware.api_auth import api_key_manager
print('Valid keys:', len(api_key_manager.valid_keys))
"
```

**Common Causes**:
- API key not generated
- Wrong header name
- Key not added to manager

---

### Issue: Validation not blocking attacks

**Check**:
```bash
# Test validator directly
python -c "
from shared.middleware.request_validator import validator
print('SQL:', validator.check_sql_injection(\"'; DROP TABLE users; --\"))
print('XSS:', validator.check_xss('<script>alert(1)</script>'))
"
```

**Common Causes**:
- Regex patterns not compiled
- Middleware not applied
- Validation skipped for certain paths

---

### Issue: Security headers missing

**Check**:
```bash
# Verify middleware order
# Security headers should be first

# Check response headers
curl -I http://localhost:8001/health | grep -i "x-"
```

**Common Causes**:
- Middleware not added
- Middleware order wrong
- Headers overwritten by other middleware

---

## Cleanup

```bash
# Stop all services
# Press Ctrl+C in each terminal

# Remove test data
rm -rf test_data/
```

---

## Verification Checklist

- [ ] All middleware files created
- [ ] Security middleware added to all agents
- [ ] API keys generated and configured
- [ ] Security headers present in responses
- [ ] Rate limiting working
- [ ] API key authentication working
- [ ] SQL injection prevention working
- [ ] XSS prevention working
- [ ] Path traversal prevention working
- [ ] Request size limits enforced
- [ ] Input validation with Pydantic working
- [ ] CORS configured correctly
- [ ] All security tests passing

---

## Expected File Structure

```
optiinfra/
├── shared/
│   ├── middleware/
│   │   ├── __init__.py                ✅
│   │   ├── rate_limiter.py            ✅
│   │   ├── request_validator.py       ✅
│   │   ├── security_headers.py        ✅
│   │   └── api_auth.py                ✅
│   ├── validation/
│   │   ├── __init__.py                ✅
│   │   └── schemas.py                 ✅
│   ├── config/
│   │   └── security.py                ✅
│   └── tests/
│       └── test_security.py           ✅
├── services/
│   ├── cost-agent/
│   │   └── src/main.py                ✅ (updated)
│   ├── performance-agent/
│   │   └── src/main.py                ✅ (updated)
│   ├── resource-agent/
│   │   └── src/main.py                ✅ (updated)
│   └── application-agent/
│       └── src/main.py                ✅ (updated)
└── ...
```

---

## Success Criteria

✅ **API Security Implemented**
- Rate limiting active
- Request validation working
- Security headers present
- API key authentication enforced

✅ **Attack Prevention**
- SQL injection blocked
- XSS blocked
- Path traversal blocked
- Request size limits enforced

✅ **Input Validation**
- Pydantic schemas defined
- Invalid input rejected
- Validation errors clear

✅ **Configuration**
- Security settings centralized
- Environment-based configuration
- API keys managed securely

---

## Performance Metrics

- **Rate Limit Overhead**: < 1ms per request
- **Validation Overhead**: < 2ms per request
- **Total Security Overhead**: < 5ms per request
- **Memory Usage**: < 50MB for rate limiter

---

## Security Best Practices Implemented

- ✅ **Defense in Depth**: Multiple layers of security
- ✅ **Fail Secure**: Deny by default
- ✅ **Least Privilege**: Minimal permissions
- ✅ **Input Validation**: Validate all inputs
- ✅ **Output Encoding**: Prevent injection
- ✅ **Secure Headers**: Browser security
- ✅ **Rate Limiting**: Prevent abuse
- ✅ **Authentication**: API key required
- ✅ **Logging**: Security events logged
- ✅ **Testing**: Comprehensive security tests

---

## Next Steps

After validation:
1. ✅ Mark PHASE5-5.7 as complete
2. 📝 Create PHASE5-5.7_COMPLETE.md
3. 🚀 Proceed to PHASE5-5.8 E2E System Tests

---

**Status**: Ready for execution ✅
