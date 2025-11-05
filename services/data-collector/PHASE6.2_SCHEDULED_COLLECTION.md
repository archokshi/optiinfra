# Phase 6.2: Scheduled Collection

**Status:** ✅ IMPLEMENTED  
**Date:** October 29, 2025

---

## 🎯 **Objective**

Implement automated scheduled data collection using Celery + Redis for background job processing.

---

## 📋 **Features Implemented**

### **1. Celery Integration** ✅
- Celery app configured with Redis broker
- Task serialization and result backend
- Task time limits and retries
- Worker prefetch and concurrency settings

### **2. Background Tasks** ✅
- `collect_data_task` - Async data collection for a single customer
- `scheduled_collection_task` - Scheduled collection for all customers
- `health_check_task` - Worker health verification

### **3. Beat Scheduler** ✅
- Scheduled collection every 15 minutes
- Cron-based scheduling
- Task expiration and retry logic

### **4. Async API Support** ✅
- `async_mode` parameter in collection endpoint
- Queue tasks via Celery
- Immediate response with task ID

### **5. Monitoring** ✅
- Flower web UI on port 5555
- Real-time task monitoring
- Worker status and statistics

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────┐
│              DATA COLLECTOR SERVICES                     │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
   ┌────▼────┐      ┌────▼────┐      ┌────▼────┐
   │ FastAPI │      │ Celery  │      │ Celery  │
   │   API   │      │ Worker  │      │  Beat   │
   │ (8005)  │      │         │      │Scheduler│
   └────┬────┘      └────┬────┘      └────┬────┘
        │                │                 │
        └────────────────┼─────────────────┘
                         │
                    ┌────▼────┐
                    │  Redis  │
                    │  Queue  │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────▼────┐      ┌────▼────┐    ┌────▼────┐
   │ClickHouse│      │PostgreSQL│    │  Redis  │
   │ Metrics  │      │ History  │    │ Events  │
   └──────────┘      └──────────┘    └──────────┘
```

---

## 📦 **New Services**

### **1. data-collector-worker**
- **Container:** `optiinfra-data-collector-worker`
- **Purpose:** Execute background collection tasks
- **Concurrency:** 2 workers
- **Dependencies:** PostgreSQL, ClickHouse, Redis

### **2. data-collector-beat**
- **Container:** `optiinfra-data-collector-beat`
- **Purpose:** Schedule periodic tasks
- **Schedule:** Every 15 minutes
- **Dependencies:** Redis, Worker

### **3. flower**
- **Container:** `optiinfra-flower`
- **Port:** 5555
- **Purpose:** Monitor Celery tasks and workers
- **URL:** http://localhost:5555

---

## 🔄 **Collection Flow**

### **Async Collection (Default)**
```
1. POST /api/v1/collect/trigger (async_mode=true)
2. FastAPI queues task to Redis
3. Returns task_id immediately
4. Celery worker picks up task
5. Worker collects data from cloud provider
6. Worker writes to ClickHouse, PostgreSQL, Redis
7. Task completes
```

### **Scheduled Collection (Every 15 minutes)**
```
1. Celery Beat triggers scheduled_collection_task
2. Task gets list of customers
3. For each customer:
   - Queue collect_data_task
   - Worker processes collection
   - Data written to databases
4. Repeat every 15 minutes
```

### **Synchronous Collection (Optional)**
```
1. POST /api/v1/collect/trigger (async_mode=false)
2. FastAPI executes collection immediately
3. Returns result when complete
4. Use for testing or immediate needs
```

---

## 🔧 **Configuration**

### **Environment Variables**

```bash
# Celery Configuration
DEFAULT_CUSTOMER_ID=default_customer  # Customer for scheduled collection
COLLECTION_INTERVAL=900  # 15 minutes in seconds

# Redis (Broker & Backend)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# Worker Settings
CELERY_CONCURRENCY=2
CELERY_MAX_TASKS_PER_CHILD=100
CELERY_TASK_TIME_LIMIT=1800  # 30 minutes
```

### **Beat Schedule**

```python
beat_schedule = {
    "collect-vultr-cost-every-15-minutes": {
        "task": "src.tasks.scheduled_collection_task",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
        "args": ("vultr", ["cost"]),
    }
}
```

---

## 📊 **API Changes**

### **Updated Endpoint: POST /api/v1/collect/trigger**

**Request:**
```json
{
  "customer_id": "alpesh_chokshi",
  "provider": "vultr",
  "data_types": ["cost"],
  "async_mode": true  // NEW: Default true
}
```

**Response (Async):**
```json
{
  "task_id": "celery-task-uuid",
  "status": "queued",
  "message": "Collection task queued for vultr",
  "started_at": "2025-10-29T...",
  "async_mode": true
}
```

**Response (Sync):**
```json
{
  "task_id": "uuid",
  "status": "completed",
  "message": "Collection completed for vultr",
  "started_at": "2025-10-29T...",
  "async_mode": false
}
```

---

## 🚀 **Usage**

### **Start All Services**
```powershell
docker-compose up -d data-collector data-collector-worker data-collector-beat flower
```

### **Trigger Async Collection**
```powershell
curl -X POST http://localhost:8005/api/v1/collect/trigger `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "test_user",
    "provider": "vultr",
    "data_types": ["cost"],
    "async_mode": true
  }'
```

### **Monitor Tasks (Flower)**
```
Open browser: http://localhost:5555
```

### **Check Worker Status**
```powershell
docker logs optiinfra-data-collector-worker
```

### **Check Beat Scheduler**
```powershell
docker logs optiinfra-data-collector-beat
```

---

## 📈 **Monitoring**

### **Flower Dashboard**
- **URL:** http://localhost:5555
- **Features:**
  - Active tasks
  - Completed tasks
  - Failed tasks
  - Worker status
  - Task statistics
  - Task history

### **Task Status**
```powershell
# Get task status
curl http://localhost:8005/api/v1/collect/status/{task_id}
```

### **Collection History**
```sql
-- PostgreSQL
SELECT * FROM collection_history 
ORDER BY started_at DESC 
LIMIT 10;
```

---

## ✅ **Testing**

### **Test 1: Health Check Task**
```python
from src.tasks import health_check_task
result = health_check_task.delay()
print(result.get())
```

### **Test 2: Async Collection**
```powershell
curl -X POST http://localhost:8005/api/v1/collect/trigger `
  -H "Content-Type: application/json" `
  -d '{"customer_id":"test","provider":"vultr","data_types":["cost"],"async_mode":true}'
```

### **Test 3: Verify Scheduled Tasks**
```powershell
# Check beat scheduler logs
docker logs optiinfra-data-collector-beat --tail 50

# Should see:
# "Scheduler: Sending due task collect-vultr-cost-every-15-minutes"
```

---

## 🎯 **Benefits**

1. **Non-Blocking API** - Immediate response, no waiting
2. **Scalable** - Add more workers as needed
3. **Reliable** - Task retries and error handling
4. **Scheduled** - Automatic collection every 15 minutes
5. **Monitorable** - Flower dashboard for visibility
6. **Fault Tolerant** - Tasks survive worker restarts

---

## 📝 **Files Created**

```
services/data-collector/
├── src/
│   ├── celery_app.py ✅ (Celery configuration)
│   ├── tasks.py ✅ (Celery tasks)
│   └── main.py ✅ (Updated with async support)
├── Dockerfile.worker ✅ (Celery worker)
├── Dockerfile.beat ✅ (Celery beat)
└── requirements.txt ✅ (Added Celery dependencies)

docker-compose.yml ✅ (Added 3 new services)
```

---

## 🔄 **Next Steps**

### **Phase 6.3: Cost Agent Refactor**
- Remove collection logic from cost-agent
- Add data readers
- Integrate with data-collector

### **Phase 6.4: Performance & Resource Collectors**
- Implement performance collectors
- Implement resource collectors
- Add to beat schedule

### **Phase 6.5: Complete Multi-Cloud**
- Implement AWS, GCP, Azure collectors
- Add to beat schedule
- Scale workers

---

## 📊 **Performance**

- **Task Queue:** Redis (fast, in-memory)
- **Worker Concurrency:** 2 (configurable)
- **Task Timeout:** 30 minutes
- **Retry Attempts:** 3
- **Retry Delay:** 60 seconds
- **Schedule Interval:** 15 minutes

---

## ✅ **Phase 6.2 Complete!**

**Status:** ✅ IMPLEMENTED  
**Services Added:** 3 (worker, beat, flower)  
**New Ports:** 5555 (Flower)  
**Scheduled Tasks:** 1 (Vultr cost collection)  
**Ready for:** Phase 6.3

---

**Implemented by:** Cascade AI  
**Date:** October 29, 2025  
**Phase:** 6.2 - Scheduled Collection
