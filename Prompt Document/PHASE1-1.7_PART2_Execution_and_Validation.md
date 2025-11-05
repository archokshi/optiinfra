# PHASE1-1.7 PART2: Analysis Engine - Execution and Validation

**Phase:** Cost Agent - Week 2  
**Objective:** Execute and validate the Analysis Engine implementation  
**Base:** PHASE1-1.7 PART1 (Code Implementation)  
**Date:** October 22, 2025

---

## 📋 OVERVIEW

This document provides step-by-step instructions for executing and validating the Analysis Engine implementation with idle detection and anomaly detection capabilities.

**Prerequisites:**
- ✅ PHASE1-1.7 PART1 completed
- ✅ Python 3.13+ environment
- ✅ All dependencies installed
- ✅ Cloud credentials configured (optional for testing)

---

## 🚀 QUICK START

### 1. Verify Environment
```bash
cd services/cost-agent
source venv/bin/activate  # or .\venv\Scripts\activate on Windows
python --version  # Should be 3.13+
```

### 2. Run Tests
```bash
pytest tests/test_analysis_engine_production.py -v
```

### 3. Expected Output
```
32+ tests collected
32+ passed
Success rate: 100%
```

---

## ✅ PRE-EXECUTION CHECKLIST

### Code Files Created
- [ ] `src/nodes/idle_detection.py`
- [ ] `src/nodes/anomaly_detection.py`
- [ ] `src/nodes/analysis_report.py`
- [ ] `src/models/analysis_engine.py`
- [ ] `src/workflows/analysis_engine.py`
- [ ] `tests/test_analysis_engine_production.py`

### Code Files Enhanced
- [ ] `src/database/clickhouse_metrics.py` (new table + methods)
- [ ] `src/monitoring/prometheus_metrics.py` (new metrics)

### Documentation Created
- [ ] `PHASE1-1.7_PART1_Code_Implementation.md`
- [ ] `PHASE1-1.7_PART2_Execution_and_Validation.md` (this file)

### Dependencies Verified
- [ ] `langgraph` installed
- [ ] `pydantic` installed
- [ ] `tenacity` installed
- [ ] `numpy` or `scipy` installed (for statistical analysis)
- [ ] `clickhouse-driver` installed (optional)
- [ ] `prometheus-client` installed

---

## 📝 STEP-BY-STEP EXECUTION

### STEP 1: Create Idle Detection Module

**File:** `src/nodes/idle_detection.py`

**Implementation Checklist:**
- [ ] Import statements (logging, typing, statistics, tenacity)
- [ ] `detect_idle_resources()` function
- [ ] `analyze_resource_utilization()` function
- [ ] `classify_idle_severity()` function
- [ ] `calculate_waste_cost()` function
- [ ] `generate_idle_recommendations()` function
- [ ] Error handling with retry logic
- [ ] Comprehensive logging

**Key Logic:**
```python
# Idle classification
if cpu_avg < 1 and memory_avg < 5:
    return "critical"  # Completely idle
elif cpu_avg < 5 and memory_avg < 10:
    return "high"  # Very low utilization
elif cpu_avg < 10 and memory_avg < 20:
    return "medium"  # Low utilization
else:
    return "low"  # Minimal activity
```

**Validation:**
```bash
# Run idle detection tests
pytest tests/test_analysis_engine_production.py::TestIdleDetection -v
```

**Expected:** 8/8 tests passing

---

### STEP 2: Create Anomaly Detection Module

**File:** `src/nodes/anomaly_detection.py`

**Implementation Checklist:**
- [ ] Import statements
- [ ] `detect_anomalies()` function
- [ ] `detect_cost_anomalies()` function
- [ ] `detect_usage_anomalies()` function
- [ ] `detect_configuration_drift()` function
- [ ] `calculate_anomaly_score()` function
- [ ] Statistical methods (Z-score, IQR)
- [ ] Error handling

**Statistical Anomaly Detection:**
```python
# Z-Score method
mean = np.mean(values)
std = np.std(values)
z_score = (current_value - mean) / std
if abs(z_score) > 2:  # 2 standard deviations
    return True  # Anomaly detected

# IQR method
Q1 = np.percentile(values, 25)
Q3 = np.percentile(values, 75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
if value < lower_bound or value > upper_bound:
    return True  # Anomaly detected
```

**Validation:**
```bash
# Run anomaly detection tests
pytest tests/test_analysis_engine_production.py::TestAnomalyDetection -v
```

**Expected:** 8/8 tests passing

---

### STEP 3: Create Analysis Report Module

**File:** `src/nodes/analysis_report.py`

**Implementation Checklist:**
- [ ] Import statements
- [ ] `generate_analysis_report()` function
- [ ] `calculate_total_waste()` function
- [ ] `prioritize_findings()` function
- [ ] `generate_executive_summary()` function
- [ ] Error handling

**Report Structure:**
```python
{
    "total_idle_resources": 15,
    "total_monthly_waste": 2500.00,
    "total_anomalies": 8,
    "top_findings": [
        {
            "type": "idle_resource",
            "resource_id": "i-123",
            "severity": "critical",
            "monthly_cost": 500.00,
            "recommendation": "terminate"
        },
        {
            "type": "cost_anomaly",
            "description": "Cost spike detected",
            "deviation": 150.0,
            "severity": "high"
        }
    ],
    "executive_summary": {
        "total_potential_savings": 2500.00,
        "critical_issues": 3,
        "recommended_actions": 12
    }
}
```

**Validation:**
```bash
# Run analysis report tests
pytest tests/test_analysis_engine_production.py::TestAnalysisReport -v
```

**Expected:** 4/4 tests passing

---

### STEP 4: Create Pydantic Models

**File:** `src/models/analysis_engine.py`

**Implementation Checklist:**
- [ ] Import statements (pydantic, datetime, typing)
- [ ] `AnalysisRequest` model
- [ ] `IdleResource` model
- [ ] `Anomaly` model
- [ ] `AnalysisReport` model
- [ ] `AnalysisResponse` model
- [ ] Field validators
- [ ] Custom validation logic

**Validation Rules:**
```python
# Customer ID
@field_validator('customer_id')
def validate_customer_id(cls, v):
    if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
        raise ValueError('Invalid customer_id format')
    return v

# Lookback period
lookback_days: int = Field(ge=1, le=30)

# Thresholds
idle_threshold_cpu: float = Field(ge=0.0, le=100.0)

# Anomaly sensitivity
anomaly_sensitivity: str = Field(pattern=r'^(low|medium|high)$')
```

**Validation:**
```bash
# Run validation tests
pytest tests/test_analysis_engine_production.py::TestValidation -v
```

**Expected:** 6/6 tests passing

---

### STEP 5: Create LangGraph Workflow

**File:** `src/workflows/analysis_engine.py`

**Implementation Checklist:**
- [ ] Import statements (langgraph, typing, logging)
- [ ] `AnalysisEngineState` TypedDict
- [ ] `ProductionAnalysisEngine` class
- [ ] `__init__()` method (initialize collectors)
- [ ] `collect_resource_data()` method
- [ ] `_collect_aws_data()` method
- [ ] `_collect_gcp_data()` method (placeholder)
- [ ] `_collect_azure_data()` method (placeholder)
- [ ] `create_workflow()` method (LangGraph setup)
- [ ] `run_analysis()` method
- [ ] Metrics integration (ClickHouse + Prometheus)
- [ ] Error handling

**Workflow Graph:**
```python
workflow = StateGraph(AnalysisEngineState)

# Add nodes
workflow.add_node("collect_data", collect_resource_data)
workflow.add_node("detect_idle", detect_idle_resources)
workflow.add_node("detect_anomalies", detect_anomalies)
workflow.add_node("generate_report", generate_analysis_report)

# Add edges
workflow.set_entry_point("collect_data")
workflow.add_edge("collect_data", "detect_idle")
workflow.add_edge("collect_data", "detect_anomalies")
workflow.add_edge("detect_idle", "generate_report")
workflow.add_edge("detect_anomalies", "generate_report")
workflow.add_edge("generate_report", END)

# Compile
app = workflow.compile()
```

**Validation:**
```bash
# Run workflow tests
pytest tests/test_analysis_engine_production.py::TestWorkflow -v
```

**Expected:** 3/3 tests passing

---

### STEP 6: Enhance ClickHouse Metrics

**File:** `src/database/clickhouse_metrics.py`

**Implementation Checklist:**
- [ ] Add `analysis_engine_events` table creation
- [ ] Add `insert_analysis_engine_event()` method
- [ ] Add `get_customer_waste_trends()` method
- [ ] Add `get_anomaly_trends()` method
- [ ] Error handling
- [ ] Logging

**Table Schema:**
```sql
CREATE TABLE IF NOT EXISTS analysis_engine_events (
    timestamp DateTime,
    request_id String,
    customer_id String,
    cloud_provider String,
    analysis_type String,
    total_resources_analyzed UInt32,
    idle_resources_found UInt32,
    critical_idle_count UInt32,
    high_idle_count UInt32,
    medium_idle_count UInt32,
    low_idle_count UInt32,
    total_monthly_waste Float64,
    total_annual_waste Float64,
    total_anomalies_found UInt32,
    cost_anomalies UInt32,
    usage_anomalies UInt32,
    config_anomalies UInt32,
    security_anomalies UInt32,
    critical_anomalies UInt32,
    high_anomalies UInt32,
    success UInt8,
    error_message String,
    duration_ms UInt32
) ENGINE = MergeTree()
ORDER BY (timestamp, customer_id)
TTL timestamp + INTERVAL 90 DAY
```

**Validation:**
```bash
# Run metrics tests
pytest tests/test_analysis_engine_production.py::TestMetrics::test_clickhouse_insert_event -v
pytest tests/test_analysis_engine_production.py::TestMetrics::test_get_waste_trends -v
```

**Expected:** 2/2 tests passing

---

### STEP 7: Enhance Prometheus Metrics

**File:** `src/monitoring/prometheus_metrics.py`

**Implementation Checklist:**
- [ ] Add counter metrics
- [ ] Add histogram metrics
- [ ] Add gauge metrics
- [ ] Add `record_analysis_engine_start()` function
- [ ] Add `record_analysis_engine_complete()` function
- [ ] Add `record_idle_resource_detected()` function
- [ ] Add `record_anomaly_detected()` function
- [ ] Add `update_waste_metrics()` function
- [ ] Error handling
- [ ] Logging

**Metrics:**
```python
# Counters
analysis_engine_runs_total
idle_resources_detected_total
anomalies_detected_total

# Histograms
idle_resource_waste_dollars
anomaly_deviation_percent
analysis_engine_duration_seconds

# Gauges
total_idle_resources
total_monthly_waste_dollars
active_anomalies
```

**Validation:**
```bash
# Run Prometheus tests
pytest tests/test_analysis_engine_production.py::TestMetrics::test_prometheus_metrics_recording -v
```

**Expected:** 1/1 test passing

---

### STEP 8: Create Comprehensive Tests

**File:** `tests/test_analysis_engine_production.py`

**Implementation Checklist:**
- [ ] Import statements (pytest, unittest.mock, etc.)
- [ ] `TestIdleDetection` class (8 tests)
- [ ] `TestAnomalyDetection` class (8 tests)
- [ ] `TestAnalysisReport` class (4 tests)
- [ ] `TestWorkflow` class (3 tests)
- [ ] `TestMetrics` class (3 tests)
- [ ] `TestValidation` class (6 tests)
- [ ] `TestIntegration` class (1 test)
- [ ] Mock data fixtures
- [ ] Async test support

**Test Structure:**
```python
class TestIdleDetection:
    def test_detect_completely_idle_resources(self):
        # Test with 0% utilization
        
    def test_detect_low_utilization_resources(self):
        # Test with < 5% utilization
        
    def test_classify_idle_severity(self):
        # Test severity classification
        
    # ... more tests
```

**Validation:**
```bash
# Run all tests
pytest tests/test_analysis_engine_production.py -v --tb=short

# Run with coverage
pytest tests/test_analysis_engine_production.py --cov=src/nodes --cov=src/workflows --cov=src/models --cov-report=term-missing
```

**Expected:** 32+/32+ tests passing, 85%+ coverage

---

## 🧪 VALIDATION TESTS

### Test 1: Completely Idle Resource Detection
```python
def test_completely_idle_detection():
    resource = {
        "resource_id": "i-idle-123",
        "metrics_history": [
            {"cpu": 0.0, "memory": 0.0, "network_in": 0.0}
            for _ in range(168)  # 7 days
        ]
    }
    
    result = analyze_resource_utilization(resource)
    assert result["idle_severity"] == "critical"
    assert result["recommendation"] == "terminate"
```

### Test 2: Cost Anomaly Detection
```python
def test_cost_spike_detection():
    cost_history = [100.0] * 30  # Normal: $100/day
    cost_history.append(500.0)  # Spike: $500/day
    
    anomalies = detect_cost_anomalies(cost_history)
    
    assert len(anomalies) > 0
    assert anomalies[0]["anomaly_type"] == "cost_spike"
    assert anomalies[0]["severity"] in ["high", "critical"]
```

### Test 3: Usage Anomaly Detection
```python
def test_usage_anomaly_detection():
    usage_history = [
        {"cpu": 50.0, "memory": 60.0}
        for _ in range(100)
    ]
    usage_history.append({"cpu": 95.0, "memory": 98.0})  # Spike
    
    anomalies = detect_usage_anomalies(usage_history)
    
    assert len(anomalies) > 0
    assert anomalies[0]["anomaly_type"] == "usage_spike"
```

### Test 4: Complete Workflow
```python
@pytest.mark.asyncio
async def test_complete_workflow():
    engine = ProductionAnalysisEngine(
        aws_credentials={"access_key": "test", "secret_key": "test"}
    )
    
    # Mock AWS collector
    engine.aws_collector = MagicMock()
    
    with patch.object(engine, '_collect_aws_data') as mock_collect:
        mock_collect.return_value = {
            "resources": [...],  # Mock resource data
            "cost_history": [...]  # Mock cost data
        }
        
        result = await engine.run_analysis(
            customer_id="customer1",
            cloud_provider="aws",
            analysis_types=["idle", "anomaly"],
            lookback_days=7
        )
        
        assert result["success"] is True
        assert "analysis_report" in result
        assert result["analysis_report"]["total_idle_resources"] >= 0
        assert result["analysis_report"]["total_anomalies"] >= 0
```

---

## 📊 SUCCESS CRITERIA

### Code Quality
- [ ] All files created
- [ ] No syntax errors
- [ ] No import errors
- [ ] Proper type hints
- [ ] Comprehensive docstrings
- [ ] PEP 8 compliant

### Testing
- [ ] 32+ tests created
- [ ] 32+ tests passing (100%)
- [ ] 85%+ code coverage
- [ ] All edge cases covered
- [ ] Integration tests passing

### Functionality
- [ ] Idle detection working
- [ ] Anomaly detection working
- [ ] Report generation complete
- [ ] Waste calculation accurate
- [ ] Recommendations appropriate

### Integration
- [ ] ClickHouse metrics working
- [ ] Prometheus metrics working
- [ ] LangGraph workflow executing
- [ ] Error handling robust
- [ ] Logging comprehensive

---

## 🐛 TROUBLESHOOTING

### Issue 1: Statistical Library Missing
**Symptom:** ImportError for numpy/scipy  
**Solution:**
```bash
pip install numpy scipy
```

### Issue 2: Anomaly Detection False Positives
**Symptom:** Too many anomalies detected  
**Solution:**
1. Adjust sensitivity threshold
2. Increase baseline period
3. Add business context filters

### Issue 3: Idle Detection Inaccurate
**Symptom:** Active resources marked as idle  
**Solution:**
1. Check metric collection
2. Verify threshold settings
3. Review idle duration requirements

---

## 📈 PERFORMANCE BENCHMARKS

### Expected Performance
- **Data Collection:** < 10s per 100 resources
- **Idle Detection:** < 2s per 100 resources
- **Anomaly Detection:** < 5s per 100 resources
- **Report Generation:** < 1s
- **Complete Workflow:** < 30s for 100 resources

### Optimization Tips
1. Cache baseline statistics
2. Parallel processing for multiple resources
3. Incremental analysis for continuous monitoring
4. Use sampling for large datasets
5. Implement result caching

---

## 📊 METRICS DASHBOARD

### Key Metrics to Monitor

**Operational Metrics:**
- Analysis runs per hour
- Average processing time
- Error rate
- Success rate

**Business Metrics:**
- Idle resources per customer
- Total waste identified
- Anomalies detected per day
- Cost savings realized

**Quality Metrics:**
- False positive rate
- False negative rate
- Detection accuracy
- Alert response time

---

## 🎯 POST-COMPLETION TASKS

### Immediate
- [ ] Run full test suite
- [ ] Verify all tests passing
- [ ] Check code coverage
- [ ] Review error handling
- [ ] Validate logging

### Short-term
- [ ] Create implementation summary
- [ ] Create validation summary
- [ ] Update main documentation
- [ ] Create usage examples
- [ ] Document known issues

### Future
- [ ] Deploy to staging
- [ ] Integration testing
- [ ] Load testing
- [ ] Performance optimization
- [ ] Production deployment

---

## 📝 VALIDATION CHECKLIST

### Code Implementation
- [ ] All 8 files created/modified
- [ ] ~3,100 lines of code added
- [ ] No syntax errors
- [ ] All imports working
- [ ] Type hints complete

### Testing
- [ ] 32+ tests created
- [ ] All tests passing
- [ ] 85%+ coverage achieved
- [ ] Edge cases covered
- [ ] Integration tests working

### Documentation
- [ ] PART1 complete
- [ ] PART2 complete (this file)
- [ ] Code comments comprehensive
- [ ] Docstrings complete
- [ ] Usage examples provided

### Integration
- [ ] ClickHouse table created
- [ ] Prometheus metrics defined
- [ ] LangGraph workflow working
- [ ] Metrics recording functional
- [ ] Error handling robust

---

## 🎉 SUCCESS INDICATORS

### You're Done When:
1. ✅ All 32+ tests passing (100%)
2. ✅ Code coverage >= 85%
3. ✅ No failing tests
4. ✅ All files created
5. ✅ Metrics integration working
6. ✅ Documentation complete
7. ✅ Example usage working
8. ✅ Ready for staging deployment

---

## 📖 EXAMPLE EXECUTION

### Running the Complete Analysis
```python
from src.workflows.analysis_engine import ProductionAnalysisEngine

# Initialize
engine = ProductionAnalysisEngine(
    aws_credentials={
        "access_key": "YOUR_KEY",
        "secret_key": "YOUR_SECRET",
        "region": "us-east-1"
    }
)

# Execute
result = await engine.run_analysis(
    customer_id="customer-123",
    cloud_provider="aws",
    analysis_types=["idle", "anomaly"],
    lookback_days=7,
    idle_threshold_cpu=5.0,
    anomaly_sensitivity="medium"
)

# Review results
report = result["analysis_report"]
print(f"Idle Resources: {report['total_idle_resources']}")
print(f"Monthly Waste: ${report['total_monthly_waste']:,.2f}")
print(f"Anomalies: {report['total_anomalies']}")

# Top findings
for finding in report['top_findings'][:5]:
    print(f"\n{finding['type'].upper()}: {finding['description']}")
    print(f"  Severity: {finding['severity']}")
    print(f"  Impact: ${finding.get('cost_impact', 0):,.2f}/month")
    print(f"  Action: {finding.get('recommendation', 'Review')}")
```

---

## 🔄 NEXT STEPS

After completing PHASE1-1.7:

1. **Validate Results** - Review all test outputs
2. **Create Summary** - Document implementation
3. **Deploy to Staging** - Test with real data
4. **Integration Testing** - Test with other workflows
5. **Production Deployment** - Roll out to customers

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Status:** Ready for Implementation  
**Estimated Time:** 2.5 hours
