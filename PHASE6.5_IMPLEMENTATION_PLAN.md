# Phase 6.5 - Application Collector + Multi-Cloud + Application Agent Refactor

**Date:** October 30, 2025  
**Status:** 🚀 STARTING  
**Duration:** 2-3 weeks

---

## 🎯 **Objective**

Extend the Unified Data Collection Architecture to include:

1. **Application Quality Monitoring** (quality, hallucinations, toxicity)
2. **Multi-Cloud Support** (AWS, GCP, Azure collectors)
3. **Application Agent Refactor** (use ClickHouse readers)
4. **Cross-Cloud Analysis**

---

## 🏗️ **Architecture Extension**

### **Current (After Phase 6.4):**
```
Data Collector
├── Cost Collectors (Vultr) ✅
├── Performance Collectors (Vultr) ✅
├── Resource Collectors (Vultr) ✅
└── Writes to ClickHouse

Cost Agent ✅
Performance Agent (needs refactor)
Resource Agent (needs refactor)
```

### **Target (Phase 6.5):**
```
Data Collector
├── Cost Collectors (Vultr, AWS, GCP, Azure) ✅
├── Performance Collectors (Vultr, AWS, GCP, Azure) ✅
├── Resource Collectors (Vultr, AWS, GCP, Azure) ✅
├── Application Collectors (NEW - Quality, Hallucinations, Toxicity)
└── Writes to ClickHouse

Cost Agent ✅
Performance Agent (REFACTOR - use readers)
Resource Agent (REFACTOR - use readers)
Application Agent (REFACTOR - use readers)
```

---

## 📋 **PART 1: Code Implementation**

### **Step 1: Extend ClickHouse Schema for Application Metrics** ⏳

**File:** `database/clickhouse/schemas/metrics.sql`

**Enhance Application Metrics Table:**
```sql
-- Enhanced application metrics table
CREATE TABLE IF NOT EXISTS optiinfra_metrics.application_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    application_id String,
    application_name String,
    metric_type String,  -- quality, hallucination, toxicity, latency, etc.
    score Float64,
    details String,
    model_name String,
    prompt_text String,
    response_text String,
    metadata String,
    collected_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, application_id, timestamp);

-- Add indexes
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_provider provider TYPE minmax GRANULARITY 4;
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_metric_type metric_type TYPE set(100) GRANULARITY 4;
ALTER TABLE application_metrics ADD INDEX IF NOT EXISTS idx_model_name model_name TYPE set(50) GRANULARITY 4;
```

---

### **Step 2: Create Application Collectors** ⏳

**Directory:** `services/data-collector/src/collectors/application/`

**Files to Create:**
- `__init__.py`
- `base_application_collector.py`
- `vultr_application_collector.py` (Groq LLM integration)
- `aws_application_collector.py` (Bedrock integration)
- `gcp_application_collector.py` (Vertex AI integration)
- `azure_application_collector.py` (Azure OpenAI integration)

**Metrics to Collect:**
- Quality scores (coherence, relevance, accuracy)
- Hallucination detection
- Toxicity/safety scores
- Response latency
- Token usage
- Model performance

---

### **Step 3: Integrate Groq LLM for Quality Analysis** ⏳

**File:** `services/data-collector/src/collectors/application/groq_client.py`

**Features:**
- Connect to Groq API
- Analyze LLM responses for quality
- Detect hallucinations
- Check for toxicity
- Generate quality scores

---

### **Step 4: Move AWS Collectors to Data-Collector** ⏳

**Files to Move/Create:**
- `services/data-collector/src/collectors/aws/cost_collector.py`
- `services/data-collector/src/collectors/aws/performance_collector.py`
- `services/data-collector/src/collectors/aws/resource_collector.py`
- `services/data-collector/src/collectors/aws/client.py` (boto3 wrapper)

**AWS Services to Collect:**
- Cost Explorer API
- CloudWatch metrics
- EC2, RDS, Lambda resources

---

### **Step 5: Move GCP Collectors to Data-Collector** ⏳

**Files to Move/Create:**
- `services/data-collector/src/collectors/gcp/cost_collector.py`
- `services/data-collector/src/collectors/gcp/performance_collector.py`
- `services/data-collector/src/collectors/gcp/resource_collector.py`
- `services/data-collector/src/collectors/gcp/client.py` (google-cloud wrapper)

**GCP Services to Collect:**
- Billing API
- Cloud Monitoring
- Compute Engine, Cloud SQL resources

---

### **Step 6: Add Azure Collectors** ⏳

**Files to Create:**
- `services/data-collector/src/collectors/azure/cost_collector.py`
- `services/data-collector/src/collectors/azure/performance_collector.py`
- `services/data-collector/src/collectors/azure/resource_collector.py`
- `services/data-collector/src/collectors/azure/client.py` (azure-sdk wrapper)

**Azure Services to Collect:**
- Cost Management API
- Azure Monitor
- VMs, SQL Database resources

---

### **Step 7: Update Storage Writers** ⏳

**File:** `services/data-collector/src/storage/clickhouse_writer.py`

**Update Method:**
- Enhance `write_application_metrics()` for new schema

---

### **Step 8: Update Celery Tasks** ⏳

**File:** `services/data-collector/src/celery_app.py`

**Add Scheduled Tasks:**
```python
'collect-application-15min': {
    'task': 'src.tasks.scheduled_collection_task',
    'schedule': crontab(minute='*/15'),
    'args': ('vultr', ['application']),
},
'collect-aws-all-15min': {
    'task': 'src.tasks.scheduled_collection_task',
    'schedule': crontab(minute='*/15'),
    'args': ('aws', ['cost', 'performance', 'resource']),
},
'collect-gcp-all-15min': {
    'task': 'src.tasks.scheduled_collection_task',
    'schedule': crontab(minute='*/15'),
    'args': ('gcp', ['cost', 'performance', 'resource']),
},
```

---

### **Step 9: Create Application Readers** ⏳

**Directory:** `services/application-agent/src/readers/`

**Files to Create:**
- `__init__.py`
- `clickhouse_reader.py`
- `application_reader.py`

**Methods:**
- `get_quality_metrics()`
- `get_hallucination_reports()`
- `get_toxicity_scores()`
- `get_model_performance()`
- `get_application_summary()`

---

### **Step 10: Create Performance/Resource Readers** ⏳

**Directories:**
- `services/performance-agent/src/readers/`
- `services/resource-agent/src/readers/`

**Files to Create:**
- `clickhouse_reader.py` (similar to cost-agent)
- `performance_reader.py` / `resource_reader.py`

---

### **Step 11: Create V2 API Routes** ⏳

**Files:**
- `services/application-agent/src/api/application_routes_v2.py`
- `services/performance-agent/src/api/performance_routes_v2.py`
- `services/resource-agent/src/api/resource_routes_v2.py`

**Application Endpoints:**
```
GET  /api/v2/applications/{customer_id}/{provider}/quality
GET  /api/v2/applications/{customer_id}/{provider}/hallucinations
GET  /api/v2/applications/{customer_id}/{provider}/toxicity
GET  /api/v2/applications/{customer_id}/{provider}/performance
POST /api/v2/applications/trigger-collection
```

**Performance Endpoints:**
```
GET  /api/v2/performance/{customer_id}/{provider}/metrics
GET  /api/v2/performance/{customer_id}/{provider}/trends
POST /api/v2/performance/trigger-collection
```

**Resource Endpoints:**
```
GET  /api/v2/resources/{customer_id}/{provider}/inventory
GET  /api/v2/resources/{customer_id}/{provider}/changes
POST /api/v2/resources/trigger-collection
```

---

### **Step 12: Add Cross-Cloud Analysis** ⏳

**File:** `services/data-collector/src/analysis/cross_cloud_analyzer.py`

**Features:**
- Compare costs across clouds
- Identify optimization opportunities
- Multi-cloud resource mapping
- Unified dashboards

---

### **Step 13: Update Main Applications** ⏳

**Files:**
- `services/application-agent/src/main.py`
- `services/performance-agent/src/main.py`
- `services/resource-agent/src/main.py`

Add V2 routes and mark legacy routes as deprecated.

---

## 📋 **PART 2: Validation**

### **Test 1: ClickHouse Schema** ✅
- Verify enhanced application_metrics table
- Check indexes

### **Test 2: Application Collectors** ✅
- Test Groq LLM integration
- Verify quality analysis
- Check hallucination detection

### **Test 3: AWS Collectors** ✅
- Test AWS cost collection
- Test AWS performance collection
- Test AWS resource collection

### **Test 4: GCP Collectors** ✅
- Test GCP cost collection
- Test GCP performance collection
- Test GCP resource collection

### **Test 5: Azure Collectors** ✅
- Test Azure cost collection
- Test Azure performance collection
- Test Azure resource collection

### **Test 6: Application Agent V2 APIs** ✅
- Test quality endpoints
- Test hallucination endpoints
- Test toxicity endpoints

### **Test 7: Performance Agent V2 APIs** ✅
- Test metrics endpoints
- Test trends endpoints
- Verify multi-cloud support

### **Test 8: Resource Agent V2 APIs** ✅
- Test inventory endpoints
- Test changes endpoints
- Verify multi-cloud support

### **Test 9: Cross-Cloud Analysis** ✅
- Test cost comparison
- Test resource mapping
- Verify unified view

### **Test 10: Integration Test** ✅
- Trigger collection for all clouds
- Verify all 4 data types collected
- Check cross-cloud queries

---

## 🎯 **Success Criteria**

| Criteria | Status |
|----------|--------|
| Application collectors added | ⏳ |
| Groq LLM integrated | ⏳ |
| AWS collectors migrated | ⏳ |
| GCP collectors migrated | ⏳ |
| Azure collectors added | ⏳ |
| Application readers created | ⏳ |
| Performance readers created | ⏳ |
| Resource readers created | ⏳ |
| V2 endpoints implemented (all agents) | ⏳ |
| Cross-cloud analysis working | ⏳ |
| All tests passing | ⏳ |
| Multi-cloud support validated | ⏳ |

---

## 📝 **Files to Create/Modify**

### **Data Collector:**
```
services/data-collector/src/collectors/application/
├── __init__.py
├── base_application_collector.py
├── vultr_application_collector.py
├── groq_client.py
├── aws_application_collector.py
├── gcp_application_collector.py
└── azure_application_collector.py

services/data-collector/src/collectors/aws/
├── __init__.py
├── client.py
├── cost_collector.py
├── performance_collector.py
└── resource_collector.py

services/data-collector/src/collectors/gcp/
├── __init__.py
├── client.py
├── cost_collector.py
├── performance_collector.py
└── resource_collector.py

services/data-collector/src/collectors/azure/
├── __init__.py
├── client.py
├── cost_collector.py
├── performance_collector.py
└── resource_collector.py

services/data-collector/src/analysis/
└── cross_cloud_analyzer.py
```

### **Application Agent:**
```
services/application-agent/src/readers/
├── __init__.py
├── clickhouse_reader.py
└── application_reader.py

services/application-agent/src/integration/
├── __init__.py
└── data_collector_client.py

services/application-agent/src/api/
└── application_routes_v2.py
```

### **Performance Agent:**
```
services/performance-agent/src/readers/
├── __init__.py
├── clickhouse_reader.py
└── performance_reader.py

services/performance-agent/src/integration/
├── __init__.py
└── data_collector_client.py

services/performance-agent/src/api/
└── performance_routes_v2.py
```

### **Resource Agent:**
```
services/resource-agent/src/readers/
├── __init__.py
├── clickhouse_reader.py
└── resource_reader.py

services/resource-agent/src/integration/
├── __init__.py
└── data_collector_client.py

services/resource-agent/src/api/
└── resource_routes_v2.py
```

---

## 📊 **Estimated Effort**

| Task | Estimated Time |
|------|----------------|
| ClickHouse schema | 15 min |
| Application collectors | 2 hours |
| Groq LLM integration | 1 hour |
| AWS collectors | 2 hours |
| GCP collectors | 2 hours |
| Azure collectors | 2 hours |
| Storage updates | 30 min |
| Celery tasks | 30 min |
| Application readers | 1 hour |
| Performance readers | 1 hour |
| Resource readers | 1 hour |
| Integration clients | 1 hour |
| V2 API routes (3 agents) | 3 hours |
| Cross-cloud analysis | 2 hours |
| Main app updates | 30 min |
| Testing | 2 hours |
| Documentation | 1 hour |
| **Total** | **~22 hours** |

---

## 🚀 **Let's Begin!**

Starting with PART 1: Code Implementation...

**First Step:** Enhance ClickHouse schema for application metrics.
