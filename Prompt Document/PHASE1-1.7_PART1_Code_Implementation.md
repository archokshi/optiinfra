# PHASE1-1.7 PART1: Analysis Engine - Code Implementation

**Phase:** Cost Agent - Week 2  
**Objective:** Implement production-ready Analysis Engine with Idle Detection and Anomaly Detection  
**Priority:** HIGH  
**Estimated Effort:** 30+25m (1.2-1.4 hours)  
**Date:** October 22, 2025

---

## 📋 OVERVIEW

The Analysis Engine is a critical component that continuously monitors cloud resources to identify:
1. **Idle Resources** - Resources consuming costs with minimal/no utilization
2. **Anomalies** - Unusual patterns in resource usage, costs, or behavior

**Key Differences from Previous Workflows:**
- **PHASE1-1.6 (Spot):** One-time migration optimization
- **PHASE1-1.6b (RI):** Commitment-based savings
- **PHASE1-1.6c (Right-Sizing):** Resource sizing optimization
- **PHASE1-1.7 (Analysis Engine):** Continuous monitoring and detection

**Expected Savings:** 15-40% through idle resource elimination and anomaly prevention

---

## 🎯 OBJECTIVES

### Primary Goals
1. **Idle Detection:**
   - Identify completely idle resources (0% utilization)
   - Detect low-utilization resources (< 5% utilization)
   - Calculate waste costs
   - Recommend termination or hibernation

2. **Anomaly Detection:**
   - Detect cost spikes (sudden increases)
   - Identify usage anomalies (unusual patterns)
   - Detect configuration drift
   - Alert on security risks (unusual access patterns)

3. **Continuous Monitoring:**
   - Real-time analysis
   - Historical trend analysis
   - Predictive alerts
   - Automated recommendations

### Success Criteria
- ✅ Accurate idle resource detection (< 1% false positives)
- ✅ Anomaly detection with configurable sensitivity
- ✅ Real-time alerting (< 5 minute latency)
- ✅ Integration with ClickHouse and Prometheus
- ✅ 85%+ test coverage

---

## 🏗️ ARCHITECTURE

### Analysis Engine Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Analysis Engine                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. collect_resource_data                                    │
│     └─> Gather metrics from cloud providers                 │
│                                                              │
│  2. detect_idle_resources                                    │
│     ├─> Analyze CPU, memory, network, disk usage            │
│     ├─> Identify completely idle resources                  │
│     ├─> Detect low-utilization resources                    │
│     └─> Calculate waste costs                               │
│                                                              │
│  3. detect_anomalies                                         │
│     ├─> Cost anomaly detection (spikes, drops)              │
│     ├─> Usage anomaly detection (unusual patterns)          │
│     ├─> Configuration drift detection                       │
│     └─> Security anomaly detection                          │
│                                                              │
│  4. generate_analysis_report                                 │
│     ├─> Aggregate findings                                  │
│     ├─> Calculate total waste                               │
│     ├─> Prioritize recommendations                          │
│     └─> Generate alerts                                     │
│                                                              │
│  5. trigger_alerts (future)                                  │
│     └─> Send notifications for critical findings            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Cloud Metrics → Idle Detection → Anomaly Detection → Analysis Report → Alerts
     ↓                ↓                  ↓                  ↓
ClickHouse      Prometheus         ClickHouse         Prometheus
```

---

## 📦 IMPLEMENTATION PLAN

### Phase 1: Idle Detection Module
**File:** `src/nodes/idle_detection.py`

**Functions:**

1. `detect_idle_resources(state) -> Dict`
   - Analyze resource utilization metrics
   - Identify idle and low-utilization resources
   - Calculate waste costs
   - Generate recommendations

2. `analyze_resource_utilization(resource) -> Dict`
   - Calculate utilization metrics (CPU, memory, network, disk)
   - Determine idle status
   - Calculate idle duration
   - Estimate cost savings

3. `classify_idle_severity(metrics) -> str`
   - Returns: "critical", "high", "medium", "low"
   - Critical: 0% utilization for 7+ days
   - High: < 1% utilization for 7+ days
   - Medium: < 5% utilization for 7+ days
   - Low: < 10% utilization for 7+ days

4. `calculate_waste_cost(resource, idle_duration) -> float`
   - Calculate total waste cost
   - Factor in resource type and pricing
   - Consider idle duration

5. `generate_idle_recommendations(idle_resources) -> List[Dict]`
   - Recommend termination for critical/high severity
   - Recommend hibernation for medium severity
   - Recommend monitoring for low severity

**Key Metrics:**
- CPU utilization (avg, p95, p99)
- Memory utilization (avg, p95, p99)
- Network throughput (in/out)
- Disk I/O (read/write operations)
- Connection count
- Request count

**Idle Criteria:**
```python
# Completely Idle
cpu_avg < 1% AND memory_avg < 5% AND network_in < 1KB/s AND disk_ops < 10/min

# Low Utilization
cpu_avg < 5% AND memory_avg < 10% AND network_in < 10KB/s

# Minimal Activity
cpu_avg < 10% AND memory_avg < 20%
```

---

### Phase 2: Anomaly Detection Module
**File:** `src/nodes/anomaly_detection.py`

**Functions:**

1. `detect_anomalies(state) -> Dict`
   - Detect cost anomalies
   - Detect usage anomalies
   - Detect configuration anomalies
   - Detect security anomalies

2. `detect_cost_anomalies(cost_history) -> List[Dict]`
   - Statistical anomaly detection (Z-score, IQR)
   - Detect sudden spikes (> 2 std dev)
   - Detect gradual increases (trend analysis)
   - Detect unexpected drops

3. `detect_usage_anomalies(usage_history) -> List[Dict]`
   - Detect unusual CPU/memory patterns
   - Detect traffic spikes
   - Detect unusual access patterns
   - Time-series anomaly detection

4. `detect_configuration_drift(current_config, baseline_config) -> List[Dict]`
   - Detect unauthorized changes
   - Detect security group modifications
   - Detect IAM policy changes
   - Detect resource tag changes

5. `calculate_anomaly_score(anomaly) -> float`
   - Score 0.0-1.0 indicating severity
   - Factor in deviation magnitude
   - Factor in historical context
   - Factor in business impact

**Anomaly Detection Methods:**
```python
# Statistical Methods
- Z-Score: (value - mean) / std_dev > threshold
- IQR: value < Q1 - 1.5*IQR or value > Q3 + 1.5*IQR
- Moving Average: value > MA + (2 * std_dev)

# Machine Learning (Future)
- Isolation Forest
- LSTM for time-series
- Autoencoder for pattern detection
```

**Anomaly Types:**
1. **Cost Anomalies:**
   - Sudden spike (> 50% increase in 1 hour)
   - Gradual increase (> 20% increase over 7 days)
   - Unexpected drop (> 30% decrease)
   - New resource type costs

2. **Usage Anomalies:**
   - CPU spike (> 90% for extended period)
   - Memory leak pattern (gradual increase)
   - Traffic spike (> 5x normal)
   - Unusual access times (off-hours activity)

3. **Configuration Anomalies:**
   - Security group opened to 0.0.0.0/0
   - IAM policy changes
   - Encryption disabled
   - Public access enabled

4. **Security Anomalies:**
   - Unusual login locations
   - Failed authentication attempts
   - Privilege escalation
   - Data exfiltration patterns

---

### Phase 3: Analysis Report Generation
**File:** `src/nodes/analysis_report.py`

**Functions:**

1. `generate_analysis_report(state) -> Dict`
   - Aggregate idle resources
   - Aggregate anomalies
   - Calculate total waste
   - Prioritize findings
   - Generate executive summary

2. `calculate_total_waste(idle_resources) -> Dict`
   - Total monthly waste
   - Total annual waste
   - Breakdown by resource type
   - Breakdown by severity

3. `prioritize_findings(idle_resources, anomalies) -> List[Dict]`
   - Sort by severity and cost impact
   - Group by category
   - Add priority scores

4. `generate_executive_summary(findings) -> Dict`
   - Key metrics
   - Top findings
   - Recommended actions
   - Potential savings

---

### Phase 4: Pydantic Models
**File:** `src/models/analysis_engine.py`

**Models:**

1. **AnalysisRequest**
```python
class AnalysisRequest(BaseModel):
    customer_id: str  # Regex: ^[a-zA-Z0-9_-]{1,64}$
    cloud_provider: str  # Enum: aws, gcp, azure
    analysis_types: List[str] = ["idle", "anomaly"]  # idle, anomaly, both
    lookback_days: int = 7  # 1-30 days
    idle_threshold_cpu: float = 5.0  # 0-100%
    idle_threshold_memory: float = 10.0  # 0-100%
    anomaly_sensitivity: str = "medium"  # low, medium, high
    include_recommendations: bool = True
```

2. **IdleResource**
```python
class IdleResource(BaseModel):
    resource_id: str
    resource_type: str  # ec2, rds, ebs, etc.
    resource_name: Optional[str]
    region: str
    
    # Utilization metrics
    cpu_avg: float
    memory_avg: float
    network_in_avg: float  # KB/s
    network_out_avg: float  # KB/s
    disk_read_ops: float
    disk_write_ops: float
    
    # Idle analysis
    idle_severity: str  # critical, high, medium, low
    idle_duration_days: int
    last_active_timestamp: datetime
    
    # Cost analysis
    hourly_cost: float
    daily_waste: float
    monthly_waste: float
    annual_waste: float
    
    # Recommendations
    recommendation: str  # terminate, hibernate, monitor
    recommendation_reason: str
    estimated_savings: float
```

3. **Anomaly**
```python
class Anomaly(BaseModel):
    anomaly_id: str
    anomaly_type: str  # cost, usage, configuration, security
    resource_id: Optional[str]
    resource_type: Optional[str]
    region: str
    
    # Detection details
    detected_at: datetime
    anomaly_score: float  # 0.0-1.0
    severity: str  # critical, high, medium, low
    
    # Anomaly specifics
    metric_name: str
    expected_value: float
    actual_value: float
    deviation_percent: float
    
    # Context
    description: str
    potential_causes: List[str]
    recommended_actions: List[str]
    
    # Impact
    cost_impact: Optional[float]
    security_impact: Optional[str]
```

4. **AnalysisReport**
```python
class AnalysisReport(BaseModel):
    report_id: str
    customer_id: str
    cloud_provider: str
    analysis_timestamp: datetime
    lookback_days: int
    
    # Idle resources
    total_idle_resources: int
    idle_resources: List[IdleResource]
    idle_by_severity: Dict[str, int]
    total_monthly_waste: float
    total_annual_waste: float
    
    # Anomalies
    total_anomalies: int
    anomalies: List[Anomaly]
    anomalies_by_type: Dict[str, int]
    anomalies_by_severity: Dict[str, int]
    
    # Summary
    executive_summary: Dict[str, Any]
    top_findings: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]
    
    # Metadata
    analysis_duration_seconds: float
    success: bool
    error_message: Optional[str]
```

5. **AnalysisResponse**
```python
class AnalysisResponse(BaseModel):
    request_id: str
    customer_id: str
    cloud_provider: str
    timestamp: datetime
    
    # Results
    analysis_report: AnalysisReport
    
    # Status
    workflow_status: str
    success: bool
    error_message: Optional[str]
```

---

### Phase 5: LangGraph Workflow
**File:** `src/workflows/analysis_engine.py`

**Workflow State:**
```python
class AnalysisEngineState(TypedDict):
    request_id: str
    customer_id: str
    cloud_provider: str
    analysis_types: List[str]
    lookback_days: int
    
    # Collected data
    resource_data: List[Dict[str, Any]]
    cost_history: List[Dict[str, Any]]
    
    # Analysis results
    idle_resources: List[Dict[str, Any]]
    anomalies: List[Dict[str, Any]]
    
    # Report
    analysis_report: Dict[str, Any]
    
    # Status
    workflow_status: str
    error_message: Optional[str]
```

**Workflow Class:**
```python
class ProductionAnalysisEngine:
    def __init__(
        self,
        aws_credentials: Optional[Dict] = None,
        gcp_credentials: Optional[Dict] = None,
        azure_credentials: Optional[Dict] = None
    ):
        # Initialize cloud collectors
        # Initialize metrics clients
        # Create workflow graph
    
    async def collect_resource_data(
        self,
        customer_id: str,
        cloud_provider: str,
        lookback_days: int
    ) -> List[Dict]:
        """Collect resource metrics and cost data"""
        
    async def run_analysis(
        self,
        customer_id: str,
        cloud_provider: str = "aws",
        analysis_types: List[str] = ["idle", "anomaly"],
        lookback_days: int = 7,
        **kwargs
    ) -> Dict:
        """Run complete analysis engine workflow"""
```

---

### Phase 6: ClickHouse Metrics Enhancement
**File:** `src/database/clickhouse_metrics.py`

**New Table:**
```sql
CREATE TABLE IF NOT EXISTS analysis_engine_events (
    timestamp DateTime,
    request_id String,
    customer_id String,
    cloud_provider String,
    analysis_type String,
    
    -- Idle detection metrics
    total_resources_analyzed UInt32,
    idle_resources_found UInt32,
    critical_idle_count UInt32,
    high_idle_count UInt32,
    medium_idle_count UInt32,
    low_idle_count UInt32,
    total_monthly_waste Float64,
    total_annual_waste Float64,
    
    -- Anomaly detection metrics
    total_anomalies_found UInt32,
    cost_anomalies UInt32,
    usage_anomalies UInt32,
    config_anomalies UInt32,
    security_anomalies UInt32,
    critical_anomalies UInt32,
    high_anomalies UInt32,
    
    -- Status
    success UInt8,
    error_message String,
    duration_ms UInt32
) ENGINE = MergeTree()
ORDER BY (timestamp, customer_id)
TTL timestamp + INTERVAL 90 DAY
```

**New Methods:**
- `insert_analysis_engine_event(event: Dict) -> None`
- `get_customer_waste_trends(customer_id: str, days: int) -> Dict`
- `get_anomaly_trends(customer_id: str, days: int) -> Dict`

---

### Phase 7: Prometheus Metrics Enhancement
**File:** `src/monitoring/prometheus_metrics.py`

**New Metrics:**

**Counters:**
```python
analysis_engine_runs_total = Counter(
    'analysis_engine_runs_total',
    'Total analysis engine runs',
    ['customer_id', 'cloud_provider', 'analysis_type', 'status']
)

idle_resources_detected_total = Counter(
    'idle_resources_detected_total',
    'Total idle resources detected',
    ['customer_id', 'resource_type', 'severity']
)

anomalies_detected_total = Counter(
    'anomalies_detected_total',
    'Total anomalies detected',
    ['customer_id', 'anomaly_type', 'severity']
)
```

**Histograms:**
```python
idle_resource_waste_dollars = Histogram(
    'idle_resource_waste_dollars',
    'Idle resource waste amount distribution',
    ['customer_id', 'resource_type'],
    buckets=[10, 50, 100, 500, 1000, 5000, 10000]
)

anomaly_deviation_percent = Histogram(
    'anomaly_deviation_percent',
    'Anomaly deviation percentage distribution',
    ['customer_id', 'anomaly_type'],
    buckets=[10, 25, 50, 100, 200, 500, 1000]
)

analysis_engine_duration_seconds = Histogram(
    'analysis_engine_duration_seconds',
    'Analysis engine execution duration',
    ['customer_id', 'cloud_provider'],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)
```

**Gauges:**
```python
total_idle_resources = Gauge(
    'total_idle_resources',
    'Current number of idle resources',
    ['customer_id', 'severity']
)

total_monthly_waste_dollars = Gauge(
    'total_monthly_waste_dollars',
    'Total monthly waste from idle resources',
    ['customer_id']
)

active_anomalies = Gauge(
    'active_anomalies',
    'Current number of active anomalies',
    ['customer_id', 'anomaly_type']
)
```

**New Functions:**
- `record_analysis_engine_start()`
- `record_analysis_engine_complete()`
- `record_idle_resource_detected()`
- `record_anomaly_detected()`
- `update_waste_metrics()`

---

## 🔒 SECURITY & VALIDATION

### Input Validation
```python
# Customer ID validation
customer_id: str = Field(
    ...,
    pattern=r'^[a-zA-Z0-9_-]{1,64}$',
    description="Customer identifier"
)

# Lookback period
lookback_days: int = Field(
    default=7,
    ge=1,
    le=30,
    description="Lookback period in days"
)

# Thresholds
idle_threshold_cpu: float = Field(
    default=5.0,
    ge=0.0,
    le=100.0,
    description="CPU idle threshold percentage"
)

# Anomaly sensitivity
anomaly_sensitivity: str = Field(
    default="medium",
    pattern=r'^(low|medium|high)$',
    description="Anomaly detection sensitivity"
)
```

### Error Handling
- Retry logic with exponential backoff
- Graceful degradation if data unavailable
- Specific exception types
- No sensitive data in logs
- Structured error messages

---

## 🧪 TESTING STRATEGY

### Test File
**File:** `tests/test_analysis_engine_production.py`

### Test Categories

1. **Idle Detection Tests** (8 tests)
   - test_detect_completely_idle_resources
   - test_detect_low_utilization_resources
   - test_classify_idle_severity
   - test_calculate_waste_cost
   - test_generate_idle_recommendations
   - test_handle_active_resources
   - test_idle_duration_calculation
   - test_edge_cases

2. **Anomaly Detection Tests** (8 tests)
   - test_detect_cost_spike_anomaly
   - test_detect_usage_anomaly
   - test_detect_configuration_drift
   - test_calculate_anomaly_score
   - test_statistical_anomaly_detection
   - test_anomaly_severity_classification
   - test_false_positive_handling
   - test_multiple_anomaly_types

3. **Analysis Report Tests** (4 tests)
   - test_generate_analysis_report
   - test_calculate_total_waste
   - test_prioritize_findings
   - test_executive_summary_generation

4. **Workflow Tests** (3 tests)
   - test_workflow_initialization
   - test_collect_resource_data
   - test_complete_analysis_workflow

5. **Metrics Tests** (3 tests)
   - test_clickhouse_insert_event
   - test_get_waste_trends
   - test_prometheus_metrics_recording

6. **Validation Tests** (6 tests)
   - test_valid_request
   - test_invalid_lookback_period
   - test_invalid_thresholds
   - test_idle_resource_validation
   - test_anomaly_validation
   - test_report_validation

**Target:** 32+ tests, 85%+ coverage

---

## 📊 SUCCESS METRICS

### Technical Metrics
- ✅ 85%+ test coverage
- ✅ All tests passing
- ✅ API response time < 30s
- ✅ Error rate < 1%
- ✅ False positive rate < 1%

### Business Metrics
- ✅ Identify 20%+ of resources as idle
- ✅ Average waste savings 15-40%
- ✅ Anomaly detection accuracy > 95%
- ✅ Alert latency < 5 minutes

### Monitoring Metrics
- ✅ Analysis runs tracked
- ✅ Idle resources per customer tracked
- ✅ Anomalies per customer tracked
- ✅ Waste trends tracked
- ✅ Processing duration tracked

---

## 🔄 INTEGRATION POINTS

### With Existing Workflows
- **PHASE1-1.6 (Spot):** Idle instances are good spot candidates
- **PHASE1-1.6b (RI):** Don't buy RIs for idle resources
- **PHASE1-1.6c (Right-Sizing):** Combine with idle detection
- **Cloud Collectors:** Reuse existing collectors
- **Metrics Infrastructure:** Reuse ClickHouse and Prometheus

### Data Sources
- CloudWatch (AWS) - Resource metrics
- Cost Explorer (AWS) - Cost data
- Cloud Monitoring (GCP) - Metrics
- Azure Monitor - Metrics
- CloudTrail/Config - Configuration changes

---

## 📝 IMPLEMENTATION STEPS

### Step 1: Create Idle Detection Module (30 min)
- Implement `idle_detection.py`
- Add utilization analysis
- Add idle classification
- Add waste calculation
- Add error handling

### Step 2: Create Anomaly Detection Module (25 min)
- Implement `anomaly_detection.py`
- Add statistical anomaly detection
- Add cost anomaly detection
- Add usage anomaly detection
- Add configuration drift detection

### Step 3: Create Analysis Report Module (15 min)
- Implement `analysis_report.py`
- Add report generation
- Add waste calculations
- Add finding prioritization

### Step 4: Create Pydantic Models (20 min)
- Implement `analysis_engine.py` (models)
- Add all validation models
- Add field validators

### Step 5: Create LangGraph Workflow (25 min)
- Implement `analysis_engine.py` (workflow)
- Create workflow graph
- Add metrics integration
- Add error handling

### Step 6: Enhance Metrics (15 min)
- Update `clickhouse_metrics.py`
- Update `prometheus_metrics.py`
- Add new tables and metrics

### Step 7: Create Tests (30 min)
- Implement `test_analysis_engine_production.py`
- Create 32+ comprehensive tests
- Achieve 85%+ coverage

### Step 8: Run and Validate (10 min)
- Run all tests
- Fix any failures
- Validate integration

**Total Estimated Time:** ~2.5 hours

---

## 🎯 DELIVERABLES

### Code Files
1. ✅ `src/nodes/idle_detection.py` (~400 lines)
2. ✅ `src/nodes/anomaly_detection.py` (~450 lines)
3. ✅ `src/nodes/analysis_report.py` (~300 lines)
4. ✅ `src/models/analysis_engine.py` (~300 lines)
5. ✅ `src/workflows/analysis_engine.py` (~500 lines)
6. ✅ `src/database/clickhouse_metrics.py` (enhanced, +150 lines)
7. ✅ `src/monitoring/prometheus_metrics.py` (enhanced, +200 lines)
8. ✅ `tests/test_analysis_engine_production.py` (~800 lines)

### Documentation
1. ✅ PHASE1-1.7_PART1_Code_Implementation.md (this file)
2. ✅ PHASE1-1.7_PART2_Execution_and_Validation.md
3. ✅ Implementation summary
4. ✅ Validation summary

**Total New Code:** ~3,100 lines

---

## 🚀 DEPLOYMENT CONSIDERATIONS

### Prerequisites
- ✅ Cloud credentials configured
- ✅ CloudWatch/monitoring access
- ✅ Cost Explorer access (AWS)
- ✅ ClickHouse server (optional)
- ✅ Prometheus server (optional)

### Configuration
```python
# Example configuration
ANALYSIS_ENGINE_CONFIG = {
    "idle_threshold_cpu": 5.0,
    "idle_threshold_memory": 10.0,
    "idle_min_duration_days": 7,
    "anomaly_sensitivity": "medium",
    "lookback_days": 7,
    "enable_alerts": True,
}
```

### Performance Considerations
- Analysis can be resource-intensive for large fleets
- Cache baseline statistics
- Parallel processing for multiple resources
- Incremental analysis for continuous monitoring

---

## 📖 EXAMPLE USAGE

```python
from src.workflows.analysis_engine import ProductionAnalysisEngine

# Initialize engine
engine = ProductionAnalysisEngine(
    aws_credentials={
        "access_key": "YOUR_ACCESS_KEY",
        "secret_key": "YOUR_SECRET_KEY",
        "region": "us-east-1"
    }
)

# Run analysis
result = await engine.run_analysis(
    customer_id="customer-123",
    cloud_provider="aws",
    analysis_types=["idle", "anomaly"],
    lookback_days=7,
    idle_threshold_cpu=5.0,
    anomaly_sensitivity="medium"
)

# Results
print(f"Idle Resources: {result['analysis_report']['total_idle_resources']}")
print(f"Monthly Waste: ${result['analysis_report']['total_monthly_waste']:,.2f}")
print(f"Anomalies: {result['analysis_report']['total_anomalies']}")

# Top findings
for finding in result['analysis_report']['top_findings']:
    print(f"- {finding['description']}: ${finding['cost_impact']:,.2f}/month")
```

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Next:** PHASE1-1.7_PART2_Execution_and_Validation.md
