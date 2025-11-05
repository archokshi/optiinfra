# Phase 6.4 - Performance & Resource Agent Refactor

**Date:** October 30, 2025  
**Status:** 🚀 STARTING

---

## 🎯 **Objective**

Extend the Unified Data Collection Architecture to include **Performance** and **Resource** metrics:

1. Add performance collectors to data-collector service
2. Add resource collectors to data-collector service
3. Extend ClickHouse schema for new metric types
4. Create performance/resource readers
5. Refactor performance-agent to use readers
6. Refactor resource-agent to use readers

---

## 🏗️ **Architecture Extension**

### **Current (After Phase 6.3):**
```
Data Collector
├── Cost Collectors ✅
└── Writes to ClickHouse (cost_metrics)

Cost Agent
├── Cost Readers ✅
└── Reads from ClickHouse
```

### **Target (Phase 6.4):**
```
Data Collector
├── Cost Collectors ✅
├── Performance Collectors (NEW)
├── Resource Collectors (NEW)
└── Writes to ClickHouse (cost, performance, resource metrics)

Cost Agent ✅
├── Cost Readers
└── Reads from ClickHouse

Performance Agent (REFACTOR)
├── Performance Readers (NEW)
└── Reads from ClickHouse

Resource Agent (REFACTOR)
├── Resource Readers (NEW)
└── Reads from ClickHouse
```

---

## 📋 **PART 1: Code Implementation**

### **Step 1: Extend ClickHouse Schema** ⏳

**File:** `database/clickhouse/schemas/metrics.sql`

**Add Tables:**
```sql
-- Performance metrics table
CREATE TABLE IF NOT EXISTS optiinfra_metrics.performance_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    metric_type String,
    resource_id String,
    resource_name String,
    metric_name String,
    metric_value Float64,
    unit String,
    metadata String,
    collected_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, resource_id, timestamp);

-- Resource metrics table
CREATE TABLE IF NOT EXISTS optiinfra_metrics.resource_metrics (
    timestamp DateTime,
    customer_id String,
    provider String,
    metric_type String,
    resource_id String,
    resource_name String,
    resource_type String,
    status String,
    region String,
    metadata String,
    collected_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (customer_id, provider, resource_id, timestamp);
```

---

### **Step 2: Add Performance Collectors** ⏳

**Directory:** `services/data-collector/src/collectors/performance/`

**Files to Create:**
- `__init__.py`
- `base_performance_collector.py`
- `vultr_performance_collector.py`
- `aws_performance_collector.py`
- `gcp_performance_collector.py`
- `azure_performance_collector.py`

**Metrics to Collect:**
- CPU utilization
- Memory utilization
- Disk I/O
- Network I/O
- Response time
- Uptime

---

### **Step 3: Add Resource Collectors** ⏳

**Directory:** `services/data-collector/src/collectors/resources/`

**Files to Create:**
- `__init__.py`
- `base_resource_collector.py`
- `vultr_resource_collector.py`
- `aws_resource_collector.py`
- `gcp_resource_collector.py`
- `azure_resource_collector.py`

**Resources to Collect:**
- Compute instances
- Storage volumes
- Databases
- Load balancers
- Networks
- Kubernetes clusters

---

### **Step 4: Update Data Collector Storage** ⏳

**File:** `services/data-collector/src/storage/clickhouse_writer.py`

**Add Methods:**
- `write_performance_metrics()`
- `write_resource_metrics()`

---

### **Step 5: Update Celery Tasks** ⏳

**File:** `services/data-collector/src/celery_app.py`

**Add Tasks:**
- `collect_performance_data_task()`
- `collect_resource_data_task()`

**Update Schedule:**
```python
'collect-performance-15min': {
    'task': 'src.celery_app.collect_performance_data_task',
    'schedule': crontab(minute='*/15'),
},
'collect-resources-15min': {
    'task': 'src.celery_app.collect_resource_data_task',
    'schedule': crontab(minute='*/15'),
}
```

---

### **Step 6: Create Performance Readers** ⏳

**Directory:** `services/performance-agent/src/readers/`

**Files to Create:**
- `__init__.py`
- `clickhouse_reader.py` (similar to cost-agent)
- `performance_reader.py`

**Methods:**
- `get_performance_metrics()`
- `get_latest_performance()`
- `get_performance_trends()`
- `get_performance_by_resource()`
- `get_performance_summary()`

---

### **Step 7: Create Resource Readers** ⏳

**Directory:** `services/resource-agent/src/readers/`

**Files to Create:**
- `__init__.py`
- `clickhouse_reader.py`
- `resource_reader.py`

**Methods:**
- `get_resources()`
- `get_resource_by_id()`
- `get_resources_by_type()`
- `get_resource_changes()`
- `get_resource_summary()`

---

### **Step 8: Create Integration Clients** ⏳

**Files:**
- `services/performance-agent/src/integration/data_collector_client.py`
- `services/resource-agent/src/integration/data_collector_client.py`

(Similar to cost-agent's integration client)

---

### **Step 9: Create V2 API Routes** ⏳

**Files:**
- `services/performance-agent/src/api/performance_routes_v2.py`
- `services/resource-agent/src/api/resource_routes_v2.py`

**Performance Endpoints:**
```
GET  /api/v2/performance/{customer_id}/{provider}/metrics
GET  /api/v2/performance/{customer_id}/{provider}/latest
GET  /api/v2/performance/{customer_id}/{provider}/trends
GET  /api/v2/performance/{customer_id}/{provider}/by-resource
GET  /api/v2/performance/{customer_id}/{provider}/summary
POST /api/v2/performance/trigger-collection
```

**Resource Endpoints:**
```
GET  /api/v2/resources/{customer_id}/{provider}/list
GET  /api/v2/resources/{customer_id}/{provider}/{resource_id}
GET  /api/v2/resources/{customer_id}/{provider}/by-type
GET  /api/v2/resources/{customer_id}/{provider}/changes
GET  /api/v2/resources/{customer_id}/{provider}/summary
POST /api/v2/resources/trigger-collection
```

---

### **Step 10: Update Main Applications** ⏳

**Files:**
- `services/performance-agent/src/main.py`
- `services/resource-agent/src/main.py`

Add V2 routes and mark legacy routes as deprecated.

---

## 📋 **PART 2: Validation**

### **Test 1: ClickHouse Schema** ✅
- Verify tables created
- Check table structure
- Test insert operations

### **Test 2: Performance Collectors** ✅
- Test Vultr performance collection
- Verify data written to ClickHouse
- Check data format

### **Test 3: Resource Collectors** ✅
- Test Vultr resource collection
- Verify data written to ClickHouse
- Check data format

### **Test 4: Performance Readers** ✅
- Test performance queries
- Verify data retrieval
- Check aggregations

### **Test 5: Resource Readers** ✅
- Test resource queries
- Verify data retrieval
- Check filtering

### **Test 6: V2 Endpoints** ✅
- Test all performance endpoints
- Test all resource endpoints
- Verify responses

### **Test 7: Integration** ✅
- Trigger performance collection
- Trigger resource collection
- Verify end-to-end flow

### **Test 8: Scheduled Collection** ✅
- Verify beat schedule
- Check worker logs
- Confirm 15-minute intervals

---

## 🎯 **Success Criteria**

| Criteria | Status |
|----------|--------|
| ClickHouse schema extended | ⏳ |
| Performance collectors added | ⏳ |
| Resource collectors added | ⏳ |
| Performance readers created | ⏳ |
| Resource readers created | ⏳ |
| V2 endpoints implemented | ⏳ |
| Integration clients created | ⏳ |
| Scheduled collection working | ⏳ |
| All tests passing | ⏳ |
| Documentation complete | ⏳ |

---

## 📝 **Files to Create**

### **Data Collector:**
```
services/data-collector/src/collectors/performance/
├── __init__.py
├── base_performance_collector.py
├── vultr_performance_collector.py
├── aws_performance_collector.py
├── gcp_performance_collector.py
└── azure_performance_collector.py

services/data-collector/src/collectors/resources/
├── __init__.py
├── base_resource_collector.py
├── vultr_resource_collector.py
├── aws_resource_collector.py
├── gcp_resource_collector.py
└── azure_resource_collector.py
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

### **Database:**
```
database/clickhouse/schemas/
└── metrics.sql (update)
```

---

## 📊 **Estimated Effort**

| Task | Estimated Time |
|------|----------------|
| ClickHouse schema | 15 min |
| Performance collectors | 1 hour |
| Resource collectors | 1 hour |
| Storage updates | 30 min |
| Celery tasks | 30 min |
| Performance readers | 45 min |
| Resource readers | 45 min |
| Integration clients | 30 min |
| V2 API routes | 1 hour |
| Main app updates | 15 min |
| Testing | 1 hour |
| Documentation | 30 min |
| **Total** | **~8 hours** |

---

## 🚀 **Let's Begin!**

Starting with PART 1: Code Implementation...

**First Step:** Extend ClickHouse schema for performance and resource metrics.
