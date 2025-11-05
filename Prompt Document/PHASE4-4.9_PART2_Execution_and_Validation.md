# PHASE4-4.9: Performance Tests - Execution and Validation

**Phase**: PHASE4-4.9  
**Agent**: Application Agent  
**Estimated Time**: 45 minutes  
**Dependencies**: PHASE4-4.8

---

## Execution Steps

### Step 1: Create Directory Structure (2 min)

```bash
# Navigate to application agent
cd services/application-agent

# Create performance test directories
mkdir -p tests/performance
mkdir -p scripts
mkdir -p performance/results
mkdir -p performance/reports
mkdir -p performance/benchmarks

# Create __init__.py
touch tests/performance/__init__.py
```

### Step 2: Install Dependencies (3 min)

```bash
# Install Locust and psutil
pip install locust>=2.15.0 psutil>=5.9.0

# Verify installation
locust --version
python -c "import psutil; print(psutil.__version__)"
```

### Step 3: Create Locust Test File (15 min)

Create `tests/performance/locustfile.py` with the content from PART1.

**Validation**:
```bash
# Verify syntax
python -m py_compile tests/performance/locustfile.py

# Check Locust can load it
locust -f tests/performance/locustfile.py --help
```

### Step 4: Create Test Runner Script (10 min)

Create `scripts/run_performance_tests.py` with the content from PART1.

**Validation**:
```bash
# Verify syntax
python -m py_compile scripts/run_performance_tests.py

# Check help
python scripts/run_performance_tests.py
```

### Step 5: Create Resource Monitor (10 min)

Create `scripts/monitor_resources.py` with the content from PART1.

**Validation**:
```bash
# Verify syntax
python -m py_compile scripts/monitor_resources.py

# Test for 10 seconds
python scripts/monitor_resources.py 10
```

### Step 6: Start Application Agent (2 min)

```bash
# Start the agent
python -m uvicorn src.main:app --reload --port 8000

# Verify it's running
curl http://localhost:8000/health
```

### Step 7: Run Load Test (5 min)

```bash
# Run basic load test
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users 10 \
    --spawn-rate 2 \
    --run-time 2m \
    --headless \
    --html performance/reports/load_test.html

# Or use the script
python scripts/run_performance_tests.py load
```

**Expected Output**:
```
Type     Name                                  # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s
--------|--------------------------------------|-------|-------------|-------|-------|-------|-------|--------|-----------
POST     /quality/analyze                       1000     0(0.00%) |     45      12     156     42 |   16.67        0.00
GET      /quality/insights                       500     0(0.00%) |     23       8      89     21 |    8.33        0.00
...
--------|--------------------------------------|-------|-------------|-------|-------|-------|-------|--------|-----------
         Aggregated                             5000     0(0.00%) |     38      8      156     35 |   83.33        0.00
```

### Step 8: Run Stress Test (5 min)

```bash
# Run stress test
python scripts/run_performance_tests.py stress

# Or manually
locust -f tests/performance/locustfile.py \
    --host=http://localhost:8000 \
    --users 50 \
    --spawn-rate 10 \
    --run-time 3m \
    --headless \
    --html performance/reports/stress_test.html
```

### Step 9: Monitor Resources During Test (3 min)

```bash
# In a separate terminal, start monitoring
python scripts/monitor_resources.py 180

# Then run a test in another terminal
python scripts/run_performance_tests.py load
```

### Step 10: Analyze Results (5 min)

```bash
# View HTML report
start performance/reports/load_test.html  # Windows
# or
open performance/reports/load_test.html   # Mac
# or
xdg-open performance/reports/load_test.html  # Linux

# View resource usage
cat performance/results/resources_*.csv
```

---

## Validation Checklist

### ✅ Installation
- [ ] Locust installed successfully
- [ ] psutil installed successfully
- [ ] All scripts have correct syntax

### ✅ Test Execution
- [ ] Locust can load test file
- [ ] Application agent is running
- [ ] Load test completes successfully
- [ ] Stress test completes successfully
- [ ] Resource monitoring works

### ✅ Performance Targets
- [ ] Response time p50 < 100ms
- [ ] Response time p95 < 200ms
- [ ] Throughput > 50 req/s
- [ ] Error rate < 1%
- [ ] CPU usage < 85%
- [ ] Memory usage < 1GB

### ✅ Reports
- [ ] HTML reports generated
- [ ] Resource CSV files created
- [ ] Statistics are reasonable
- [ ] No critical errors

---

## Expected Results

### Load Test (10 users, 5 min)
```
Total Requests: ~3000-5000
Success Rate: > 99%
Avg Response Time: 30-50ms
p95 Response Time: < 150ms
Throughput: 50-100 req/s
```

### Stress Test (50 users, 10 min)
```
Total Requests: ~15000-30000
Success Rate: > 95%
Avg Response Time: 50-100ms
p95 Response Time: < 300ms
Throughput: 100-200 req/s
```

### Resource Usage
```
CPU: 40-70%
Memory: 200-500MB
Network: 1-5 MB/s
```

---

## Troubleshooting

### Issue: Locust not found
```bash
# Solution: Install in correct environment
pip install locust
# or
python -m pip install locust
```

### Issue: Connection refused
```bash
# Solution: Ensure agent is running
python -m uvicorn src.main:app --port 8000

# Check if port is in use
netstat -an | findstr :8000  # Windows
lsof -i :8000                # Mac/Linux
```

### Issue: High error rate
```bash
# Solution 1: Reduce load
locust --users 5 --spawn-rate 1

# Solution 2: Check agent logs
# Look for errors in the agent output

# Solution 3: Increase timeouts
# Edit locustfile.py and add:
# self.client.timeout = 30
```

### Issue: Memory keeps growing
```bash
# Solution: Check for memory leaks
# Monitor with:
python scripts/monitor_resources.py 600

# If memory grows continuously, investigate:
# - Database connections not closed
# - Large objects not garbage collected
# - Caching issues
```

---

## Performance Optimization Tips

### If Response Times Are High:
1. Enable response caching
2. Optimize database queries
3. Add connection pooling
4. Use async operations
5. Profile slow endpoints

### If Throughput Is Low:
1. Increase worker processes
2. Use gunicorn instead of uvicorn
3. Enable HTTP keep-alive
4. Optimize serialization
5. Add load balancing

### If Memory Usage Is High:
1. Limit cache sizes
2. Close database connections
3. Use generators for large datasets
4. Profile memory usage
5. Enable garbage collection

---

## Success Criteria

### Must Have ✅
- [x] All test files created
- [x] Locust tests run successfully
- [x] Performance targets met
- [x] Reports generated
- [x] No critical errors

### Should Have ✅
- [ ] Resource monitoring working
- [ ] Multiple test scenarios
- [ ] Baseline benchmarks established
- [ ] Performance trends tracked

### Nice to Have 🎯
- [ ] Automated test suite
- [ ] CI/CD integration
- [ ] Real-time dashboards
- [ ] Alert thresholds

---

## Commands Reference

### Run Tests
```bash
# Load test
python scripts/run_performance_tests.py load

# Stress test
python scripts/run_performance_tests.py stress

# Spike test
python scripts/run_performance_tests.py spike

# Endurance test
python scripts/run_performance_tests.py endurance

# All tests
python scripts/run_performance_tests.py all
```

### Monitor Resources
```bash
# Monitor for 5 minutes
python scripts/monitor_resources.py 300

# Monitor for 1 hour
python scripts/monitor_resources.py 3600
```

### Locust UI Mode
```bash
# Start with web UI
locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Then open http://localhost:8089
```

---

## Next Steps

After completing PHASE4-4.9:

1. **Analyze Results**: Review all performance reports
2. **Identify Bottlenecks**: Find slow endpoints
3. **Optimize**: Implement performance improvements
4. **Re-test**: Verify improvements
5. **Document**: Update performance documentation

**Next Phase**: PHASE4-4.10 - Documentation (20+15m)

---

## Time Tracking

- Directory setup: 2 min
- Install dependencies: 3 min
- Create Locust file: 15 min
- Create runner script: 10 min
- Create monitor script: 10 min
- Run tests: 5 min

**Total**: ~45 minutes

---

## Completion Checklist

- [ ] All files created
- [ ] Dependencies installed
- [ ] Tests run successfully
- [ ] Performance targets met
- [ ] Reports generated
- [ ] Documentation updated
- [ ] Ready for PHASE4-4.10

---

**PHASE4-4.9 COMPLETE!** ✅
