# PHASE1-1.6 PART1: Spot Migration Workflow (Production) - Code Implementation

**Document Version:** 1.0  
**Date:** October 22, 2025  
**Phase:** Cost Agent - Week 2  
**Status:** Ready for Implementation  
**Base:** Extends PILOT-05 to Production Level

**Prerequisites:** 
- ✅ PILOT-05 (Spot Migration Workflow) completed
- ✅ PHASE1-1.2-1.4 (AWS/GCP/Azure Collectors) completed
- ✅ PHASE1-1.5 (LangGraph Setup) completed

---

## 📋 OVERVIEW

### Purpose
**Productionize PILOT-05** spot migration workflow by adding:
- Real cloud integration (AWS/GCP/Azure)
- Production error handling & retry logic
- Comprehensive logging & monitoring
- Security hardening & validation
- ClickHouse metrics storage
- Prometheus monitoring
- 85%+ test coverage

### Time Estimate
**Total:** ~120 minutes (2 hours)

### Success Criteria
✅ Real AWS/GCP/Azure integration  
✅ Production error handling  
✅ Comprehensive logging  
✅ Security validation  
✅ ClickHouse metrics storage  
✅ Prometheus metrics  
✅ 85%+ test coverage  
✅ Production deployment ready

---

## 🆕 WHAT'S NEW FROM PILOT-05

| Feature | PILOT-05 | PHASE1-1.6 (Production) |
|---------|----------|-------------------------|
| **Cloud Integration** | AWS Simulator | Real AWS/GCP/Azure collectors |
| **Error Handling** | Basic try-catch | Retry logic, specific exceptions |
| **Logging** | Simple logging | Structured logging with context |
| **Security** | No validation | Input validation, sanitization |
| **Performance** | Sequential | Parallel processing with asyncio |
| **Metrics** | Console only | ClickHouse + Prometheus |
| **Testing** | Basic tests | 85%+ coverage, integration tests |
| **Deployment** | Dev only | Production-ready config |

---

## 🏗 IMPLEMENTATION STEPS

### Step 1: Enhance Spot Migration Workflow

**File:** `src/workflows/spot_migration.py` (MODIFY)

**Add:**
```python
from src.collectors.aws import AWSCostCollector
from src.collectors.gcp import GCPCostCollector
from src.collectors.azure import AzureCostCollector

class ProductionSpotMigrationWorkflow:
    def __init__(self, aws_creds=None, gcp_creds=None, azure_creds=None):
        self.aws_collector = AWSCostCollector(aws_creds) if aws_creds else None
        self.gcp_collector = GCPCostCollector(gcp_creds) if gcp_creds else None
        self.azure_collector = AzureCostCollector(azure_creds) if azure_creds else None
    
    async def collect_instances(self, customer_id: str, cloud_provider: str):
        if cloud_provider == "aws":
            return await self.aws_collector.collect_ec2_instances()
        elif cloud_provider == "gcp":
            return await self.gcp_collector.collect_compute_instances()
        elif cloud_provider == "azure":
            return await self.azure_collector.collect_vm_instances()
```

---

### Step 2: Add Production Error Handling

**File:** `src/nodes/spot_analyze.py` (ENHANCE)

**Add:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def analyze_spot_opportunities(state: SpotMigrationState):
    try:
        # Analysis logic
        ...
    except AWSThrottlingError as e:
        logger.warning(f"AWS throttling, retrying: {e}")
        raise
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        return {"workflow_status": "failed", "error_message": str(e)}
    except Exception as e:
        logger.exception("Unexpected error")
        raise
```

---

### Step 3: Add ClickHouse Metrics Storage

**File:** `src/database/clickhouse_metrics.py` (NEW)

**Create:**
```python
class SpotMigrationMetrics:
    def __init__(self):
        self.client = Client(host=settings.CLICKHOUSE_HOST)
        self._ensure_tables()
    
    def _ensure_tables(self):
        self.client.execute("""
            CREATE TABLE IF NOT EXISTS spot_migration_events (
                timestamp DateTime,
                request_id String,
                customer_id String,
                total_savings Float64,
                success UInt8
            ) ENGINE = MergeTree()
            ORDER BY (timestamp, customer_id)
            TTL timestamp + INTERVAL 90 DAY
        """)
    
    async def insert_migration_event(self, event: Dict):
        self.client.execute("INSERT INTO spot_migration_events VALUES", [event])
```

---

### Step 4: Add Prometheus Metrics

**File:** `src/monitoring/prometheus_metrics.py` (NEW)

**Create:**
```python
from prometheus_client import Counter, Histogram, Gauge

spot_migrations_total = Counter('spot_migrations_total', 'Total migrations', ['customer_id', 'status'])
spot_migration_duration = Histogram('spot_migration_duration_seconds', 'Duration', ['phase'])
spot_savings_amount = Histogram('spot_savings_dollars', 'Savings', ['customer_id'])

def record_migration_complete(customer_id, duration, savings):
    spot_migrations_total.labels(customer_id=customer_id, status='success').inc()
    spot_migration_duration.labels(phase='complete').observe(duration)
    spot_savings_amount.labels(customer_id=customer_id).observe(savings)
```

---

### Step 5: Add Security Validation

**File:** `src/models/spot_migration.py` (ENHANCE)

**Add:**
```python
from pydantic import BaseModel, Field, validator
import re

class SpotMigrationRequest(BaseModel):
    customer_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]{1,64}$')
    instance_ids: Optional[List[str]] = Field(None, max_items=1000)
    
    @validator('instance_ids')
    def validate_instance_ids(cls, v):
        if v:
            for instance_id in v:
                if not re.match(r'^i-[a-f0-9]{8,17}$', instance_id):
                    raise ValueError(f"Invalid instance ID: {instance_id}")
        return v
```

---

### Step 6: Add Comprehensive Logging

**File:** `src/nodes/spot_analyze.py` (ENHANCE)

**Replace simple logging with structured logging:**
```python
logger.info(
    "Starting spot migration analysis",
    extra={
        "request_id": state["request_id"],
        "customer_id": state["customer_id"],
        "instance_count": len(state["ec2_instances"]),
        "cloud_provider": "aws",
        "workflow_phase": "analyze"
    }
)
```

---

### Step 7: Add Production Tests

**File:** `tests/test_spot_production.py` (NEW)

**Create:**
```python
import pytest
from unittest.mock import Mock, patch

class TestProductionSpotWorkflow:
    @pytest.mark.asyncio
    async def test_real_aws_integration(self):
        workflow = ProductionSpotMigrationWorkflow(aws_credentials={...})
        with patch('src.collectors.aws.AWSCostCollector.collect_ec2_instances') as mock:
            mock.return_value = [{"instance_id": "i-123"}]
            instances = await workflow.collect_instances("customer1", "aws")
            assert len(instances) == 1
    
    @pytest.mark.asyncio
    async def test_error_retry_logic(self):
        # Test retry on throttling
        ...
    
    @pytest.mark.asyncio
    async def test_clickhouse_storage(self):
        # Test metrics storage
        ...
```

---

## 📊 INTEGRATION POINTS

### 1. AWS Collector
```python
from src.collectors.aws import AWSCostCollector
collector = AWSCostCollector(credentials)
instances = await collector.collect_ec2_instances()
```

### 2. ClickHouse Storage
```python
from src.database.clickhouse_metrics import SpotMigrationMetrics
metrics = SpotMigrationMetrics()
await metrics.insert_migration_event({...})
```

### 3. Prometheus Metrics
```python
from src.monitoring.prometheus_metrics import record_migration_complete
record_migration_complete(customer_id, duration, savings)
```

---

## 🧪 TESTING STRATEGY

### Test Coverage: 85%+

**Unit Tests:**
- Real collector integration
- Error handling & retries
- Metrics storage
- Security validation

**Integration Tests:**
- End-to-end workflow
- Multi-cloud support
- Rollback scenarios

**Performance Tests:**
- < 2s per phase
- Parallel processing
- Database performance

---

## 📝 DEPLOYMENT

### Environment Variables
```bash
# Cloud Credentials
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
GCP_SERVICE_ACCOUNT_KEY=...
AZURE_TENANT_ID=...

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=9000

# Monitoring
PROMETHEUS_PORT=9090
```

### Production Checklist
- [ ] Cloud credentials configured
- [ ] ClickHouse tables created
- [ ] Prometheus metrics exposed
- [ ] Logging configured
- [ ] Error monitoring setup
- [ ] Tests passing (85%+)
- [ ] Security review complete

---

## 🎯 SUCCESS METRICS

**Technical:**
- 85%+ test coverage ✅
- < 2s per workflow phase ✅
- Zero data loss ✅

**Business:**
- 30-40% cost savings ✅
- Zero downtime migrations ✅
- Auto-rollback on quality issues ✅

---

## 📚 REFERENCES

- **PILOT-05:** Base implementation
- **PHASE1-1.2-1.4:** Cloud collectors
- **PHASE1-1.5:** LangGraph setup

---

**Next:** PHASE1-1.6 PART2 (Execution & Validation)

**Document Version:** 1.0  
**Last Updated:** October 22, 2025
