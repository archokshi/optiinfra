# Load Testing Guide

Comprehensive guide for load testing the Resource Agent using Locust.

---

## Quick Start

### 1. Install Locust

```bash
pip install locust
```

### 2. Start Resource Agent

```bash
cd services/resource-agent
python -m uvicorn src.main:app --port 8003
```

### 3. Run Load Test

```bash
cd tests/load
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 1m --host http://localhost:8003
```

---

## Load Test Scenarios

### Smoke Test (1 user, 1 minute)
Quick validation that all endpoints are working.

```bash
locust -f locustfile.py --headless --users 1 --spawn-rate 1 --run-time 1m --host http://localhost:8003
```

### Light Load (10 users, 5 minutes)
Typical monitoring load.

```bash
locust -f locustfile.py --headless --users 10 --spawn-rate 2 --run-time 5m --host http://localhost:8003
```

### Medium Load (50 users, 5 minutes)
Normal production load.

```bash
locust -f locustfile.py --headless --users 50 --spawn-rate 5 --run-time 5m --host http://localhost:8003
```

### Heavy Load (100 users, 3 minutes)
Peak production load.

```bash
locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 3m --host http://localhost:8003
```

### Stress Test (200 users, 2 minutes)
Find breaking point.

```bash
locust -f locustfile.py --headless --users 200 --spawn-rate 20 --run-time 2m --host http://localhost:8003
```

---

## Using Locust Web UI

### Start Locust with Web Interface

```bash
cd tests/load
locust -f locustfile.py --host http://localhost:8003
```

### Access Web UI

Open browser to: http://localhost:8089

### Configure Test

1. Enter number of users
2. Enter spawn rate (users/second)
3. Click "Start swarming"

### Monitor in Real-Time

- View requests per second
- Monitor response times
- Track error rates
- See charts and graphs

---

## Generating Reports

### HTML Report

```bash
locust -f locustfile.py --headless \
  --users 50 --spawn-rate 5 --run-time 3m \
  --host http://localhost:8003 \
  --html=results/report.html
```

### CSV Reports

```bash
locust -f locustfile.py --headless \
  --users 50 --spawn-rate 5 --run-time 3m \
  --host http://localhost:8003 \
  --csv=results/test
```

Generates:
- `results/test_stats.csv` - Request statistics
- `results/test_failures.csv` - Failure details
- `results/test_stats_history.csv` - Historical data

---

## Performance Targets

### Response Time SLAs

| Endpoint | P50 | P95 | P99 | Max |
|----------|-----|-----|-----|-----|
| `/health/` | < 10ms | < 20ms | < 50ms | < 100ms |
| `/system/metrics` | < 100ms | < 200ms | < 500ms | < 1000ms |
| `/analysis/` | < 500ms | < 1000ms | < 2000ms | < 3000ms |
| `/lmcache/status` | < 50ms | < 100ms | < 200ms | < 500ms |
| `/optimize/run` | < 1000ms | < 2000ms | < 3000ms | < 5000ms |

### Throughput SLAs

| Load Level | Users | Min RPS | Max Error Rate |
|------------|-------|---------|----------------|
| Light | 10 | 10 | 0.1% |
| Medium | 50 | 40 | 0.5% |
| Heavy | 100 | 80 | 1% |
| Stress | 200 | 100 | 5% |

---

## Interpreting Results

### Request Statistics

```
Type     Name                # reqs  # fails  |  Avg   Min   Max  Median  | req/s failures/s
---------|-------------------|--------|---------|------|-----|------|--------|-------|----------
GET      /health/             1000       0     |   12     5    45      10  |  16.7      0.00
GET      /system/metrics       500       0     |  150    80   450     140  |   8.3      0.00
```

**Key Metrics:**
- **# reqs**: Total requests
- **# fails**: Failed requests
- **Avg**: Average response time
- **Median**: 50th percentile
- **req/s**: Requests per second

### Response Time Percentiles

```
Type     Name                50%   66%   75%   80%   90%   95%   98%   99%  99.9%  100%
---------|-------------------|-----|-----|-----|-----|-----|-----|-----|-----|------|-----
GET      /health/            10    12    15    18    25    35    40    45     45    45
```

**Understanding Percentiles:**
- **P50 (Median)**: 50% of requests faster than this
- **P95**: 95% of requests faster than this
- **P99**: 99% of requests faster than this
- **P100 (Max)**: Slowest request

### What to Look For

**Good Performance:**
- ✅ Low average response times
- ✅ Consistent percentiles (P95 close to P50)
- ✅ Zero or very low error rate
- ✅ High requests per second

**Performance Issues:**
- ❌ High average response times
- ❌ Large gap between P50 and P99
- ❌ Increasing error rate
- ❌ Low requests per second

---

## Troubleshooting

### High Response Times

**Possible Causes:**
- Server overloaded
- Database slow queries
- Network latency
- Insufficient resources

**Solutions:**
- Scale horizontally (more instances)
- Optimize slow endpoints
- Add caching
- Increase server resources

### High Error Rate

**Possible Causes:**
- Connection timeouts
- Server crashes
- Resource exhaustion
- Rate limiting

**Solutions:**
- Check server logs
- Increase connection limits
- Fix memory leaks
- Add error handling

### Low Throughput

**Possible Causes:**
- Slow endpoints
- Blocking operations
- Single-threaded bottleneck
- Database connection pool exhausted

**Solutions:**
- Use async operations
- Increase worker processes
- Optimize database queries
- Add connection pooling

---

## Best Practices

### 1. Start Small
Begin with smoke tests, then gradually increase load.

### 2. Monitor Resources
Watch CPU, memory, and network during tests.

### 3. Run Multiple Times
Run each test 3-5 times to get consistent results.

### 4. Test in Isolation
Ensure no other processes interfere with tests.

### 5. Use Realistic Scenarios
Simulate actual user behavior patterns.

### 6. Document Results
Keep records of test results for comparison.

---

## Advanced Usage

### Custom User Classes

```python
from locust import HttpUser, task, between

class CustomUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(5)
    def my_task(self):
        self.client.get("/my/endpoint")
```

### Distributed Load Testing

Run on multiple machines:

```bash
# Master
locust -f locustfile.py --master --host http://localhost:8003

# Workers (on other machines)
locust -f locustfile.py --worker --master-host=<master-ip>
```

### Custom Events

```python
from locust import events

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("Test starting!")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("Test complete!")
```

---

## Continuous Performance Testing

### CI/CD Integration

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on: [push]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start Resource Agent
        run: |
          python -m uvicorn src.main:app --port 8003 &
          sleep 5
      - name: Run Load Tests
        run: |
          pip install locust
          cd tests/load
          locust -f locustfile.py --headless \
            --users 50 --spawn-rate 5 --run-time 2m \
            --host http://localhost:8003 \
            --html=report.html
      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: performance-report
          path: tests/load/report.html
```

---

## Performance Optimization Tips

### 1. Enable Production Mode
Disable debug mode and reload in production.

### 2. Use Async Operations
Leverage FastAPI's async capabilities.

### 3. Add Caching
Cache expensive operations (metrics, analysis).

### 4. Optimize Database Queries
Use indexes and query optimization.

### 5. Connection Pooling
Reuse database and HTTP connections.

### 6. Horizontal Scaling
Run multiple instances behind a load balancer.

---

## Example Results

### Good Performance Example

```
Summary:
  Total requests: 5000
  Successful: 5000 (100%)
  Failed: 0 (0%)
  Average response time: 150ms
  Requests per second: 83.3
  P95 response time: 450ms
```

### Performance Issue Example

```
Summary:
  Total requests: 5000
  Successful: 4500 (90%)
  Failed: 500 (10%)
  Average response time: 2500ms
  Requests per second: 25.0
  P95 response time: 8000ms
```

---

## Resources

- **Locust Documentation**: https://docs.locust.io/
- **Performance Testing Best Practices**: https://locust.io/
- **FastAPI Performance**: https://fastapi.tiangolo.com/deployment/

---

**Happy Load Testing!** 🚀
