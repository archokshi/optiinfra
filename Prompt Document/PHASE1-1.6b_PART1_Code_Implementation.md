# PHASE1-1.6b PART1: Reserved Instance Workflow - Code Implementation

**Phase:** Cost Agent - Week 2  
**Workflow:** Reserved Instance (RI) Optimization  
**Type:** Production Implementation  
**Date:** October 22, 2025

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [What's New from PHASE1-1.6](#whats-new-from-phase1-16)
3. [Architecture](#architecture)
4. [Implementation Steps](#implementation-steps)
5. [Code Components](#code-components)
6. [Integration Points](#integration-points)
7. [Testing Strategy](#testing-strategy)
8. [Deployment](#deployment)
9. [Success Metrics](#success-metrics)

---

## 🎯 OVERVIEW

### Purpose
Implement a production-ready Reserved Instance (RI) optimization workflow that analyzes customer workloads, recommends optimal RI purchases, and tracks savings. This extends the cost optimization suite with commitment-based savings.

### Key Features
- **Multi-Cloud RI Analysis**: AWS, GCP (Committed Use Discounts), Azure (Reserved VM Instances)
- **Usage Pattern Analysis**: Historical usage data to identify stable workloads
- **RI Recommendation Engine**: Optimal RI type, term, and payment options
- **ROI Calculation**: Break-even analysis and savings projections
- **Purchase Workflow**: Multi-agent coordination for RI procurement
- **Metrics & Monitoring**: ClickHouse + Prometheus integration
- **Security**: Input validation and sanitization

### Scope
- ✅ RI analysis for EC2, RDS, ElastiCache (AWS)
- ✅ Committed Use Discounts for Compute Engine (GCP)
- ✅ Reserved VM Instances (Azure)
- ✅ 1-year and 3-year term recommendations
- ✅ All payment options (All Upfront, Partial Upfront, No Upfront)
- ✅ Coverage and utilization tracking

---

## 🆕 WHAT'S NEW FROM PHASE1-1.6

### Similarities with Spot Migration (1.6)
- ✅ LangGraph workflow orchestration
- ✅ Multi-agent coordination
- ✅ ClickHouse metrics storage
- ✅ Prometheus monitoring
- ✅ Security validation
- ✅ Error handling with retry logic

### Key Differences
| Feature | Spot Migration (1.6) | Reserved Instance (1.6b) |
|---------|---------------------|--------------------------|
| **Analysis Type** | Interruption tolerance | Usage pattern stability |
| **Time Horizon** | Real-time | Historical (30-90 days) |
| **Commitment** | None | 1-year or 3-year |
| **Risk** | Interruption | Under-utilization |
| **Savings** | 60-90% | 30-75% |
| **Complexity** | Medium | High (ROI calculations) |
| **Services** | EC2 only | EC2, RDS, ElastiCache, etc. |

### New Components
1. **RI Analysis Engine** - Historical usage pattern analysis
2. **RI Recommendation Engine** - Optimal RI selection algorithm
3. **ROI Calculator** - Break-even and savings projections
4. **Coverage Tracker** - RI coverage and utilization monitoring
5. **Purchase Coordinator** - Multi-step RI procurement workflow

---

## 🏗️ ARCHITECTURE

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                  RI Optimization Workflow                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Data Collection                                   │
│  - Collect instance usage (30-90 days)                      │
│  - Collect current RI inventory                             │
│  - Collect pricing data                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Usage Analysis                                    │
│  - Identify stable workloads (>80% uptime)                  │
│  - Calculate average utilization                            │
│  - Detect usage patterns (steady, growing, seasonal)        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3: RI Recommendation                                 │
│  - Match instances to RI types                              │
│  - Calculate savings for each option                        │
│  - Recommend optimal term (1yr vs 3yr)                      │
│  - Recommend payment option                                 │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4: ROI Analysis                                      │
│  - Calculate break-even point                               │
│  - Project 1-year and 3-year savings                        │
│  - Risk assessment (utilization risk)                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 5: Coordination & Approval                           │
│  - Generate purchase recommendations                        │
│  - Request customer approval                                │
│  - Track approval status                                    │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 6: Execution (Optional)                              │
│  - Purchase RIs via cloud APIs                              │
│  - Update RI inventory                                      │
│  - Record metrics                                           │
└─────────────────────────────────────────────────────────────┘
```

### LangGraph State Structure

```python
class RIWorkflowState(TypedDict):
    """State for RI optimization workflow"""
    # Request metadata
    request_id: str
    customer_id: str
    cloud_provider: str
    
    # Configuration
    analysis_period_days: int  # 30, 60, or 90
    min_uptime_percent: float  # Default 80%
    service_types: List[str]  # ["ec2", "rds", "elasticache"]
    
    # Data collection
    instance_usage: List[Dict[str, Any]]
    current_ris: List[Dict[str, Any]]
    pricing_data: Dict[str, Any]
    
    # Analysis results
    stable_workloads: List[Dict[str, Any]]
    usage_patterns: Dict[str, Any]
    
    # Recommendations
    ri_recommendations: List[Dict[str, Any]]
    total_savings: float
    roi_analysis: Dict[str, Any]
    
    # Workflow control
    workflow_status: str
    current_phase: str
    success: bool
    error_message: Optional[str]
    
    # Metrics
    metrics: Dict[str, Any]
    timestamp: str
```

---

## 🔧 IMPLEMENTATION STEPS

### Step 1: Create RI Analysis Module

**File:** `src/nodes/ri_analyze.py`

**Purpose:** Analyze historical usage patterns to identify RI candidates

**Key Functions:**
```python
def analyze_usage_patterns(state: RIWorkflowState) -> RIWorkflowState:
    """
    Analyze instance usage over time to identify stable workloads.
    
    Criteria for RI candidates:
    - Uptime > 80% (configurable)
    - Consistent usage pattern
    - No planned termination
    - Cost > $50/month (minimum threshold)
    """
    
def calculate_utilization_metrics(usage_data: List[Dict]) -> Dict:
    """
    Calculate utilization metrics:
    - Average CPU utilization
    - Memory utilization
    - Network utilization
    - Uptime percentage
    """
    
def detect_usage_pattern(usage_data: List[Dict]) -> str:
    """
    Detect usage pattern type:
    - "steady": Consistent usage
    - "growing": Increasing trend
    - "seasonal": Periodic spikes
    - "declining": Decreasing trend
    """
```

**Error Handling:**
- Custom exceptions: `RIAnalysisError`, `InsufficientUsageDataError`
- Retry logic for API calls
- Graceful degradation for missing data

---

### Step 2: Create RI Recommendation Engine

**File:** `src/nodes/ri_recommend.py`

**Purpose:** Generate optimal RI purchase recommendations

**Key Functions:**
```python
def generate_ri_recommendations(state: RIWorkflowState) -> RIWorkflowState:
    """
    Generate RI recommendations based on usage analysis.
    
    For each stable workload:
    1. Match to RI offering
    2. Calculate savings for 1yr and 3yr terms
    3. Compare payment options
    4. Recommend optimal configuration
    """
    
def calculate_ri_savings(
    instance_type: str,
    on_demand_cost: float,
    ri_cost: float,
    term: str,
    payment_option: str
) -> Dict[str, float]:
    """
    Calculate savings for RI purchase:
    - Monthly savings
    - Annual savings
    - Total savings over term
    - Savings percentage
    - Break-even months
    """
    
def recommend_payment_option(
    upfront_cost: float,
    monthly_savings: float,
    customer_preferences: Dict
) -> str:
    """
    Recommend payment option based on:
    - Customer cash flow preferences
    - Break-even analysis
    - Total savings comparison
    """
```

**RI Matching Logic:**
```python
# AWS EC2 RI Types
- Standard RI: Fixed instance type, region
- Convertible RI: Flexible instance type
- Regional RI: Any AZ in region
- Zonal RI: Specific AZ

# GCP Committed Use Discounts
- Compute-optimized
- Memory-optimized
- General-purpose

# Azure Reserved VM Instances
- VM size flexibility
- Instance size flexibility
```

---

### Step 3: Create ROI Calculator

**File:** `src/nodes/ri_roi.py`

**Purpose:** Calculate ROI and break-even analysis

**Key Functions:**
```python
def calculate_roi_analysis(state: RIWorkflowState) -> RIWorkflowState:
    """
    Perform comprehensive ROI analysis:
    - Break-even point calculation
    - NPV (Net Present Value)
    - IRR (Internal Rate of Return)
    - Risk assessment
    """
    
def calculate_breakeven_point(
    upfront_cost: float,
    monthly_savings: float
) -> int:
    """
    Calculate months to break even.
    Formula: upfront_cost / monthly_savings
    """
    
def assess_utilization_risk(
    usage_pattern: str,
    uptime_percent: float,
    historical_variance: float
) -> Dict[str, Any]:
    """
    Assess risk of under-utilization:
    - Low risk: Steady pattern, >90% uptime
    - Medium risk: Growing/seasonal, 80-90% uptime
    - High risk: Declining pattern, <80% uptime
    """
```

---

### Step 4: Create RI Workflow with LangGraph

**File:** `src/workflows/ri_optimization.py`

**Purpose:** Orchestrate the complete RI optimization workflow

**Workflow Structure:**
```python
class ProductionRIOptimizationWorkflow:
    """Production RI optimization workflow"""
    
    def __init__(
        self,
        aws_credentials: Optional[Dict] = None,
        gcp_credentials: Optional[Dict] = None,
        azure_credentials: Optional[Dict] = None
    ):
        """Initialize with cloud credentials"""
        
    async def collect_usage_data(
        self,
        customer_id: str,
        cloud_provider: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Collect historical usage data"""
        
    def create_workflow(self) -> StateGraph:
        """
        Create LangGraph workflow:
        
        collect_data → analyze_usage → generate_recommendations
              ↓              ↓                    ↓
        calculate_roi → coordinate_approval → execute_purchase
        """
        
    async def run_optimization(
        self,
        customer_id: str,
        cloud_provider: str = "aws",
        service_types: List[str] = ["ec2"],
        analysis_period_days: int = 30
    ) -> Dict[str, Any]:
        """Execute complete RI optimization workflow"""
```

**LangGraph Nodes:**
1. `collect_usage_data` - Gather historical usage
2. `analyze_usage_patterns` - Identify RI candidates
3. `generate_ri_recommendations` - Create recommendations
4. `calculate_roi_analysis` - ROI and break-even
5. `coordinate_approval` - Request customer approval
6. `execute_purchase` - Purchase RIs (optional)

---

### Step 5: Add RI Metrics Storage

**File:** `src/database/clickhouse_metrics.py` (ENHANCE)

**New Table:**
```sql
CREATE TABLE IF NOT EXISTS ri_optimization_events (
    timestamp DateTime,
    request_id String,
    customer_id String,
    cloud_provider String,
    service_type String,
    workflow_phase String,
    
    -- Analysis metrics
    instances_analyzed UInt32,
    stable_workloads_found UInt32,
    analysis_period_days UInt16,
    
    -- Recommendation metrics
    ris_recommended UInt32,
    total_upfront_cost Float64,
    monthly_savings Float64,
    annual_savings Float64,
    three_year_savings Float64,
    average_breakeven_months Float32,
    
    -- RI details
    one_year_ris UInt32,
    three_year_ris UInt32,
    standard_ris UInt32,
    convertible_ris UInt32,
    
    -- Workflow status
    success UInt8,
    error_message String,
    duration_ms UInt32
) ENGINE = MergeTree()
ORDER BY (timestamp, customer_id)
TTL timestamp + INTERVAL 90 DAY
```

**New Methods:**
```python
async def insert_ri_optimization_event(
    self,
    event: Dict[str, Any]
) -> None:
    """Insert RI optimization event"""
    
async def get_customer_ri_savings(
    self,
    customer_id: str,
    days: int = 30
) -> Dict[str, Any]:
    """Get customer RI savings summary"""
    
async def get_ri_coverage_metrics(
    self,
    customer_id: str
) -> Dict[str, Any]:
    """Get RI coverage and utilization metrics"""
```

---

### Step 6: Add RI Prometheus Metrics

**File:** `src/monitoring/prometheus_metrics.py` (ENHANCE)

**New Metrics:**
```python
# Counters
ri_optimizations_total = Counter(
    'ri_optimizations_total',
    'Total RI optimizations',
    ['customer_id', 'cloud_provider', 'status']
)

ri_recommendations_total = Counter(
    'ri_recommendations_total',
    'Total RI recommendations generated',
    ['customer_id', 'service_type', 'term']
)

# Histograms
ri_savings_amount_dollars = Histogram(
    'ri_savings_amount_dollars',
    'RI savings amount distribution',
    ['customer_id', 'term']
)

ri_breakeven_months = Histogram(
    'ri_breakeven_months',
    'RI break-even period distribution',
    ['customer_id', 'payment_option']
)

ri_optimization_duration_seconds = Histogram(
    'ri_optimization_duration_seconds',
    'RI optimization duration',
    ['customer_id', 'cloud_provider']
)

# Gauges
ri_coverage_percent = Gauge(
    'ri_coverage_percent',
    'RI coverage percentage',
    ['customer_id', 'service_type']
)

ri_utilization_percent = Gauge(
    'ri_utilization_percent',
    'RI utilization percentage',
    ['customer_id', 'service_type']
)
```

**New Functions:**
```python
def record_ri_optimization_start(customer_id: str, cloud_provider: str):
    """Record RI optimization start"""
    
def record_ri_optimization_complete(
    customer_id: str,
    cloud_provider: str,
    duration: float,
    savings: float,
    recommendations: int
):
    """Record RI optimization completion"""
    
def record_ri_recommendation(
    customer_id: str,
    service_type: str,
    term: str,
    savings: float,
    breakeven_months: int
):
    """Record individual RI recommendation"""
    
def update_ri_coverage(customer_id: str, service_type: str, coverage: float):
    """Update RI coverage metric"""
```

---

### Step 7: Add Security Validation

**File:** `src/models/ri_optimization.py` (NEW)

**Pydantic Models:**
```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional
import re

class RIOptimizationRequest(BaseModel):
    """Request model for RI optimization"""
    
    customer_id: str = Field(
        ...,
        description="Customer identifier",
        min_length=1,
        max_length=64
    )
    
    cloud_provider: str = Field(
        ...,
        description="Cloud provider (aws, gcp, azure)"
    )
    
    service_types: List[str] = Field(
        default=["ec2"],
        description="Service types to analyze"
    )
    
    analysis_period_days: int = Field(
        default=30,
        ge=7,
        le=90,
        description="Analysis period in days (7-90)"
    )
    
    min_uptime_percent: float = Field(
        default=80.0,
        ge=50.0,
        le=100.0,
        description="Minimum uptime percentage for RI candidates"
    )
    
    min_monthly_cost: float = Field(
        default=50.0,
        ge=0.0,
        description="Minimum monthly cost threshold"
    )
    
    model_config = ConfigDict(str_strip_whitespace=True)
    
    @field_validator('customer_id')
    @classmethod
    def validate_customer_id(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError('Invalid customer_id format')
        return v
    
    @field_validator('cloud_provider')
    @classmethod
    def validate_cloud_provider(cls, v: str) -> str:
        if v not in ['aws', 'gcp', 'azure']:
            raise ValueError('Unsupported cloud provider')
        return v
    
    @field_validator('service_types')
    @classmethod
    def validate_service_types(cls, v: List[str]) -> List[str]:
        valid_services = {
            'ec2', 'rds', 'elasticache', 'redshift',  # AWS
            'compute', 'sql',  # GCP
            'vm', 'sql-db'  # Azure
        }
        for service in v:
            if service not in valid_services:
                raise ValueError(f'Invalid service type: {service}')
        return v


class RIRecommendation(BaseModel):
    """Single RI recommendation"""
    
    instance_type: str
    service_type: str
    region: str
    term: str  # "1year" or "3year"
    payment_option: str  # "all_upfront", "partial_upfront", "no_upfront"
    quantity: int
    
    on_demand_cost_monthly: float
    ri_cost_upfront: float
    ri_cost_monthly: float
    
    monthly_savings: float
    annual_savings: float
    total_savings: float
    savings_percent: float
    breakeven_months: int
    
    risk_level: str  # "low", "medium", "high"
    confidence_score: float  # 0.0 to 1.0


class RIOptimizationResponse(BaseModel):
    """Response model for RI optimization"""
    
    request_id: str
    customer_id: str
    cloud_provider: str
    
    instances_analyzed: int
    stable_workloads_found: int
    recommendations: List[RIRecommendation]
    
    total_upfront_cost: float
    total_monthly_savings: float
    total_annual_savings: float
    total_three_year_savings: float
    
    average_breakeven_months: float
    overall_risk_level: str
    
    workflow_status: str
    success: bool
    error_message: Optional[str] = None
    
    timestamp: str
    
    model_config = ConfigDict(str_strip_whitespace=True)
```

---

## 🔗 INTEGRATION POINTS

### 1. Cloud Collectors Integration
```python
# AWS
from src.collectors.aws import EC2CostCollector, RDSCostCollector

# Collect EC2 usage history
ec2_collector = EC2CostCollector()
usage_data = await ec2_collector.collect_usage_history(days=30)

# Collect current RIs
ri_inventory = await ec2_collector.collect_reserved_instances()

# GCP
from src.collectors.gcp import GCPBaseCollector

# Collect Compute Engine usage
gcp_collector = GCPBaseCollector()
usage_data = await gcp_collector.collect_compute_usage(days=30)

# Azure
from src.collectors.azure import AzureBaseCollector

# Collect VM usage
azure_collector = AzureBaseCollector()
usage_data = await azure_collector.collect_vm_usage(days=30)
```

### 2. Pricing API Integration
```python
# AWS Pricing API
from src.utils.pricing import AWSPricingClient

pricing_client = AWSPricingClient()
ri_prices = await pricing_client.get_ri_prices(
    instance_type="t3.large",
    region="us-east-1",
    term="1year",
    payment_option="partial_upfront"
)

# GCP Pricing API
from src.utils.pricing import GCPPricingClient

pricing_client = GCPPricingClient()
cud_prices = await pricing_client.get_cud_prices(
    machine_type="n1-standard-4",
    region="us-central1",
    term="1year"
)
```

### 3. ClickHouse Integration
```python
from src.database.clickhouse_metrics import get_metrics_client

metrics = get_metrics_client()
await metrics.insert_ri_optimization_event({
    "request_id": request_id,
    "customer_id": customer_id,
    "ris_recommended": len(recommendations),
    "annual_savings": total_savings,
    # ... other fields
})
```

### 4. Prometheus Integration
```python
from src.monitoring.prometheus_metrics import (
    record_ri_optimization_start,
    record_ri_optimization_complete,
    record_ri_recommendation
)

record_ri_optimization_start(customer_id, cloud_provider)
# ... run optimization ...
record_ri_optimization_complete(
    customer_id, cloud_provider, duration, savings, len(recommendations)
)
```

---

## 🧪 TESTING STRATEGY

### Unit Tests
**File:** `tests/test_ri_production.py`

**Test Classes:**
1. `TestRIAnalysis` - Usage pattern analysis
2. `TestRIRecommendation` - Recommendation engine
3. `TestROICalculation` - ROI and break-even
4. `TestRIWorkflow` - LangGraph workflow
5. `TestRIMetrics` - ClickHouse and Prometheus
6. `TestRIValidation` - Security validation

**Test Coverage:**
- ✅ Usage pattern detection (steady, growing, seasonal)
- ✅ RI matching logic
- ✅ Savings calculations
- ✅ Break-even analysis
- ✅ Payment option recommendations
- ✅ Multi-cloud support
- ✅ Error handling and retry
- ✅ Metrics recording
- ✅ Input validation

### Integration Tests
- ✅ End-to-end workflow execution
- ✅ Real collector integration (mocked)
- ✅ ClickHouse storage
- ✅ Prometheus metrics

### Example Tests:
```python
def test_identify_stable_workloads():
    """Test identification of RI candidates"""
    usage_data = [
        {"uptime_percent": 95, "cost_monthly": 100},
        {"uptime_percent": 75, "cost_monthly": 200},  # Too low uptime
        {"uptime_percent": 90, "cost_monthly": 30},   # Too low cost
    ]
    
    stable = identify_stable_workloads(usage_data, min_uptime=80, min_cost=50)
    
    assert len(stable) == 1
    assert stable[0]["uptime_percent"] == 95

def test_calculate_ri_savings():
    """Test RI savings calculation"""
    savings = calculate_ri_savings(
        on_demand_cost=100,
        ri_upfront=500,
        ri_monthly=60,
        term="1year"
    )
    
    assert savings["monthly_savings"] == 40
    assert savings["annual_savings"] == 480
    assert savings["breakeven_months"] == 13  # 500 / 40

def test_recommend_payment_option():
    """Test payment option recommendation"""
    option = recommend_payment_option(
        all_upfront={"upfront": 1000, "monthly": 0, "total_savings": 500},
        partial_upfront={"upfront": 500, "monthly": 30, "total_savings": 480},
        no_upfront={"upfront": 0, "monthly": 70, "total_savings": 360},
        customer_preference="maximize_savings"
    )
    
    assert option == "all_upfront"
```

---

## 🚀 DEPLOYMENT

### Prerequisites
- ✅ PHASE1-1.6 (Spot Migration) completed
- ✅ Cloud collectors operational
- ✅ ClickHouse server configured
- ✅ Prometheus server configured
- ✅ Cloud credentials configured

### Deployment Steps
1. Deploy new code to staging
2. Run comprehensive tests
3. Validate with test customer
4. Deploy to production
5. Monitor metrics

### Configuration
```python
# config.py additions
RI_ANALYSIS_PERIOD_DAYS = 30  # Default analysis period
RI_MIN_UPTIME_PERCENT = 80.0  # Minimum uptime for RI candidates
RI_MIN_MONTHLY_COST = 50.0    # Minimum cost threshold
RI_MAX_RECOMMENDATIONS = 100  # Max recommendations per request
```

---

## 📊 SUCCESS METRICS

### Technical Metrics
- ✅ All tests passing (target: 100%)
- ✅ Code coverage > 85%
- ✅ API response time < 5s
- ✅ Error rate < 1%

### Business Metrics
- ✅ RI recommendations generated
- ✅ Projected annual savings
- ✅ Average break-even period
- ✅ RI coverage improvement
- ✅ Customer approval rate

### Monitoring Metrics
- ✅ Optimization requests per day
- ✅ Average recommendations per customer
- ✅ Average savings per recommendation
- ✅ Error rate by phase
- ✅ Processing duration

---

## 📝 IMPLEMENTATION CHECKLIST

- [ ] Create `src/nodes/ri_analyze.py`
- [ ] Create `src/nodes/ri_recommend.py`
- [ ] Create `src/nodes/ri_roi.py`
- [ ] Create `src/workflows/ri_optimization.py`
- [ ] Create `src/models/ri_optimization.py`
- [ ] Enhance `src/database/clickhouse_metrics.py`
- [ ] Enhance `src/monitoring/prometheus_metrics.py`
- [ ] Create `tests/test_ri_production.py`
- [ ] Create pricing utility modules
- [ ] Update documentation
- [ ] Run all tests
- [ ] Deploy to staging

---

## 🔄 NEXT STEPS

After PHASE1-1.6b completion:
1. **PHASE1-1.6c**: Right-Sizing Workflow
2. **PHASE1-1.7**: Multi-workflow orchestration
3. **PHASE1-1.8**: LLM-powered recommendations

---

**Document Version:** 1.0  
**Last Updated:** October 22, 2025  
**Status:** Ready for Implementation
