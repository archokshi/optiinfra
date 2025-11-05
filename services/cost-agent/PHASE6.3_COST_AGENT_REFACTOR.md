# Phase 6.3 - Cost Agent Refactor

**Date:** October 30, 2025  
**Status:** 🚀 IN PROGRESS

---

## 🎯 **Objective**

Refactor the cost-agent to work with the new **Unified Data Collection Architecture**:

1. **Remove** data collection logic from cost-agent
2. **Add** data readers to fetch from ClickHouse
3. **Integrate** with data-collector service
4. **Focus** cost-agent on analysis and recommendations only

---

## 🏗️ **Architecture Change**

### **OLD Architecture (Phase 1-5):**
```
Cost Agent
├── Collectors (Vultr, AWS, GCP, Azure)
│   └── Collects data directly from cloud APIs
├── Analyzers
│   └── Analyzes collected data
└── Recommendations
    └── Generates recommendations
```

### **NEW Architecture (Phase 6.3):**
```
Data Collector Service
├── Collectors (Vultr, AWS, GCP, Azure)
│   └── Collects data from cloud APIs
│   └── Writes to ClickHouse
│   └── Scheduled every 15 minutes
└── Credentials from Database

Cost Agent
├── Data Readers (NEW)
│   └── Reads from ClickHouse
├── Analyzers
│   └── Analyzes data from ClickHouse
└── Recommendations
    └── Generates recommendations
```

---

## 📋 **PART 1: Code Implementation**

### **Step 1: Create Data Readers** ✅

**File:** `src/readers/__init__.py`
**File:** `src/readers/clickhouse_reader.py`
**File:** `src/readers/cost_reader.py`

**Purpose:**
- Read cost metrics from ClickHouse
- Replace direct cloud API calls
- Provide unified interface for all providers

**Methods:**
- `get_cost_metrics(customer_id, provider, start_date, end_date)`
- `get_latest_costs(customer_id, provider)`
- `get_cost_trends(customer_id, provider, days=30)`
- `get_cost_by_resource(customer_id, provider)`

---

### **Step 2: Remove Collection Logic** ✅

**Files to Modify:**
- `src/collectors/` - Mark as deprecated or remove
- `src/main.py` - Remove collection endpoints
- `src/api/` - Remove collection routes

**Keep:**
- Collector interfaces (for reference)
- Data models

**Remove:**
- Direct API calls to cloud providers
- Collection scheduling logic
- API key management in cost-agent

---

### **Step 3: Update Analyzers** ✅

**Files to Modify:**
- `src/analyzers/cost_analyzer.py`
- `src/analyzers/trend_analyzer.py`
- `src/analyzers/anomaly_detector.py`

**Changes:**
- Use `CostReader` instead of collectors
- Fetch data from ClickHouse
- Keep analysis logic unchanged

---

### **Step 4: Add Data-Collector Integration** ✅

**File:** `src/integration/data_collector_client.py`

**Purpose:**
- Trigger data collection on-demand
- Check collection status
- View collection history

**Methods:**
- `trigger_collection(customer_id, provider, data_types)`
- `get_collection_status(task_id)`
- `get_collection_history(customer_id)`

---

### **Step 5: Update API Endpoints** ✅

**File:** `src/api/cost_routes.py`

**Changes:**
- Remove: `POST /collect` (moved to data-collector)
- Keep: `GET /costs` (now reads from ClickHouse)
- Keep: `GET /analysis` (uses CostReader)
- Keep: `GET /recommendations`
- Add: `POST /trigger-collection` (proxies to data-collector)

---

## 📋 **PART 2: Validation**

### **Step 1: Test Data Readers** ✅
- Verify ClickHouse connection
- Test cost metrics retrieval
- Validate data format

### **Step 2: Test Analyzers** ✅
- Run analysis with ClickHouse data
- Verify recommendations generation
- Check LLM integration

### **Step 3: Test Integration** ✅
- Trigger collection via cost-agent
- Verify data flows to ClickHouse
- Confirm cost-agent reads new data

### **Step 4: End-to-End Test** ✅
- Full workflow: Trigger → Collect → Analyze → Recommend
- Verify all components work together
- Check performance

---

## 🎯 **Success Criteria**

| Criteria | Status |
|----------|--------|
| Data readers implemented | ⏳ |
| Collection logic removed | ⏳ |
| Analyzers updated | ⏳ |
| Data-collector integration | ⏳ |
| API endpoints updated | ⏳ |
| Tests passing | ⏳ |
| End-to-end flow working | ⏳ |

---

## 📝 **Files to Create**

```
src/readers/
├── __init__.py
├── clickhouse_reader.py
└── cost_reader.py

src/integration/
├── __init__.py
└── data_collector_client.py

tests/
├── test_readers.py
├── test_integration.py
└── test_end_to_end.py
```

---

## 📝 **Files to Modify**

```
src/analyzers/
├── cost_analyzer.py (use CostReader)
├── trend_analyzer.py (use CostReader)
└── anomaly_detector.py (use CostReader)

src/api/
└── cost_routes.py (update endpoints)

src/main.py (remove collection routes)
```

---

## 📝 **Files to Deprecate/Remove**

```
src/collectors/
├── vultr_collector.py (move to data-collector)
├── aws_collector.py (move to data-collector)
├── gcp_collector.py (move to data-collector)
└── azure_collector.py (move to data-collector)
```

---

## 🔄 **Migration Strategy**

### **Phase 1: Add New (Non-Breaking)**
1. Create data readers
2. Add data-collector integration
3. Keep old collectors for now

### **Phase 2: Update (Gradual)**
1. Update analyzers to use readers
2. Add new API endpoints
3. Test both old and new paths

### **Phase 3: Remove (Breaking)**
1. Remove old collection endpoints
2. Remove collector code
3. Update documentation

---

## 📊 **Expected Benefits**

### **Separation of Concerns:**
- ✅ Data collection → data-collector service
- ✅ Data analysis → cost-agent
- ✅ Clear responsibilities

### **Scalability:**
- ✅ Scale collection independently
- ✅ Scale analysis independently
- ✅ Better resource utilization

### **Maintainability:**
- ✅ Single source of truth for data
- ✅ Easier to add new providers
- ✅ Simpler testing

### **Performance:**
- ✅ Scheduled collection (no on-demand delays)
- ✅ Cached data in ClickHouse
- ✅ Faster analysis

---

## 🚀 **Let's Begin!**

Starting with PART 1: Code Implementation...
