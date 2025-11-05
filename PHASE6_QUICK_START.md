# Phase 6 - Quick Start Guide

**Last Updated:** October 30, 2025

---

## 🚀 **Quick Start: Using the New Architecture**

This guide shows you how to use the new Unified Data Collection Architecture.

---

## 📋 **Prerequisites**

✅ All services running:
```powershell
docker-compose ps
```

Expected services:
- `optiinfra-data-collector` (port 8005)
- `optiinfra-data-collector-worker`
- `optiinfra-data-collector-beat`
- `optiinfra-flower` (port 5555)
- `optiinfra-cost-agent` (port 8001)
- `optiinfra-postgres` (port 5432)
- `optiinfra-clickhouse` (ports 9000, 8123)
- `optiinfra-redis` (port 6379)

---

## 1️⃣ **Add Cloud Credentials**

### **Step 1: Add Vultr API Key**

```powershell
$body = @{
    provider = "vultr"
    credential_name = "Production Vultr"
    credentials = @{
        api_key = "YOUR-ACTUAL-VULTR-API-KEY"
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8005/api/v1/credentials" `
  -ContentType "application/json" `
  -Body $body
```

**Response:**
```json
{
  "credential_id": "uuid-here",
  "message": "Credential 'Production Vultr' created successfully",
  "provider": "vultr"
}
```

### **Step 2: Verify Credentials**

```powershell
curl http://localhost:8005/api/v1/credentials
```

---

## 2️⃣ **Trigger Data Collection**

### **Option A: Via Data-Collector (Direct)**

```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "vultr"
    data_types = @("cost")
    async_mode = $true
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8005/api/v1/collect/trigger" `
  -ContentType "application/json" `
  -Body $body
```

### **Option B: Via Cost-Agent (Recommended)**

```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "vultr"
    data_types = @("cost")
} | ConvertTo-Json

curl -Method POST `
  -Uri "http://localhost:8001/api/v2/costs/trigger-collection" `
  -ContentType "application/json" `
  -Body $body
```

**Response:**
```json
{
  "task_id": "uuid-here",
  "status": "queued",
  "message": "Collection task queued for vultr"
}
```

---

## 3️⃣ **Check Collection Status**

```powershell
curl "http://localhost:8001/api/v2/costs/collection-status/TASK-ID-HERE"
```

Or check Flower UI:
```
http://localhost:5555
```

---

## 4️⃣ **View Collected Data**

### **Get Total Cost:**

```powershell
curl "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/vultr/total?days=30"
```

### **Get Cost Trends:**

```powershell
curl "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/vultr/trends?days=7&group_by=day"
```

### **Get Costs by Resource:**

```powershell
curl "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/vultr/by-resource?days=30"
```

### **Get Latest Costs:**

```powershell
curl "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/vultr/latest?limit=100"
```

---

## 5️⃣ **View Collection History**

```powershell
curl "http://localhost:8001/api/v2/costs/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11/collection-history?limit=10"
```

Or query PostgreSQL directly:
```powershell
docker exec optiinfra-postgres psql -U optiinfra -d optiinfra -c "SELECT * FROM collection_history ORDER BY started_at DESC LIMIT 10;"
```

---

## 6️⃣ **Monitor Services**

### **Health Checks:**

```powershell
# Data Collector
curl http://localhost:8005/health

# Cost Agent
curl http://localhost:8001/api/v1/health
```

### **Flower UI (Celery Monitoring):**

Open in browser:
```
http://localhost:5555
```

### **Check Worker Logs:**

```powershell
docker logs optiinfra-data-collector-worker --tail 50
```

### **Check Beat Scheduler:**

```powershell
docker logs optiinfra-data-collector-beat --tail 50
```

---

## 7️⃣ **Query ClickHouse Directly**

### **Check Data:**

```powershell
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT COUNT(*) FROM optiinfra_metrics.cost_metrics"
```

### **View Recent Metrics:**

```powershell
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT * FROM optiinfra_metrics.cost_metrics ORDER BY timestamp DESC LIMIT 10 FORMAT Pretty"
```

### **Get Cost Summary:**

```powershell
docker exec optiinfra-clickhouse clickhouse-client --query "
SELECT 
    provider,
    sum(cost) as total_cost,
    count() as metric_count
FROM optiinfra_metrics.cost_metrics
WHERE customer_id = 'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11'
GROUP BY provider
FORMAT Pretty"
```

---

## 🔄 **Scheduled Collection**

Collection runs **automatically every 15 minutes** via Celery Beat.

To check the schedule:
```powershell
docker logs optiinfra-data-collector-beat
```

You should see:
```
[2025-10-30 ...] beat: Starting...
Scheduler: celery.beat.PersistentScheduler
```

---

## 🎯 **Common Tasks**

### **Restart All Services:**

```powershell
docker-compose restart data-collector data-collector-worker data-collector-beat cost-agent
```

### **View All Logs:**

```powershell
docker-compose logs -f data-collector data-collector-worker data-collector-beat
```

### **Rebuild After Code Changes:**

```powershell
docker-compose build --no-cache data-collector cost-agent
docker-compose up -d --force-recreate data-collector cost-agent
```

---

## 📊 **API Endpoints Summary**

### **Data Collector (Port 8005):**
```
POST   /api/v1/collect/trigger          - Trigger collection
GET    /api/v1/collect/status/{id}      - Check status
GET    /api/v1/collect/history          - View history
POST   /api/v1/credentials              - Add credentials
GET    /api/v1/credentials              - List credentials
DELETE /api/v1/credentials/{id}         - Remove credentials
GET    /health                          - Health check
```

### **Cost Agent V2 (Port 8001):**
```
GET  /api/v2/costs/{customer}/{provider}/metrics      - Get metrics
GET  /api/v2/costs/{customer}/{provider}/latest       - Get latest
GET  /api/v2/costs/{customer}/{provider}/trends       - Get trends
GET  /api/v2/costs/{customer}/{provider}/by-resource  - By resource
GET  /api/v2/costs/{customer}/{provider}/by-type      - By type
GET  /api/v2/costs/{customer}/{provider}/total        - Total cost
POST /api/v2/costs/trigger-collection                 - Trigger
GET  /api/v2/costs/collection-status/{id}             - Status
GET  /api/v2/costs/{customer}/collection-history      - History
```

---

## 🐛 **Troubleshooting**

### **Problem: No data in ClickHouse**

**Solution:**
1. Check if credentials are added
2. Trigger collection manually
3. Check worker logs for errors
4. Verify API key is valid

### **Problem: Worker not processing tasks**

**Solution:**
```powershell
# Check worker status
docker logs optiinfra-data-collector-worker

# Restart worker
docker-compose restart data-collector-worker
```

### **Problem: Beat scheduler not running**

**Solution:**
```powershell
# Check beat logs
docker logs optiinfra-data-collector-beat

# Restart beat
docker-compose restart data-collector-beat
```

### **Problem: 404 on V2 endpoints**

**Solution:**
```powershell
# Rebuild cost-agent
docker-compose build --no-cache cost-agent
docker-compose up -d --force-recreate cost-agent
```

---

## 📚 **Additional Resources**

- **Phase 6.1 Docs:** `services/data-collector/README.md`
- **Phase 6.2 Docs:** `services/data-collector/PHASE6.2_SCHEDULED_COLLECTION.md`
- **Phase 6.3 Docs:** `services/cost-agent/PHASE6.3_COMPLETE.md`
- **Credential Management:** `CUSTOMER_CREDENTIAL_MANAGEMENT.md`
- **Complete Summary:** `PHASE6_COMPLETE_SUMMARY.md`

---

## ✅ **Checklist**

- [ ] All services running
- [ ] Credentials added
- [ ] Collection triggered
- [ ] Data in ClickHouse
- [ ] V2 endpoints working
- [ ] Flower UI accessible
- [ ] Scheduled collection active

---

**Need Help?** Check the documentation files or review the logs!

🎉 **You're ready to use the new Unified Data Collection Architecture!**
