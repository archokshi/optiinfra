# Phase 6.1 PART 2: Validation Guide

This guide will help you validate the data-collector service implementation.

---

## Prerequisites

1. **Docker Desktop** must be running
2. **VULTR_API_KEY** environment variable must be set
3. **PostgreSQL, ClickHouse, Redis** services must be running

---

## Step 1: Start Required Services

```powershell
cd C:\Users\alpes\OneDrive\Documents\Important Projects\optiinfra

# Start core infrastructure
docker-compose up -d postgres clickhouse redis
```

**Expected Output:**
```
✅ optiinfra-postgres ... done
✅ optiinfra-clickhouse ... done
✅ optiinfra-redis ... done
```

**Verify:**
```powershell
docker ps | Select-String "postgres|clickhouse|redis"
```

---

## Step 2: Initialize Database Schemas

### ClickHouse Schemas

```powershell
# Connect to ClickHouse
docker exec -it optiinfra-clickhouse clickhouse-client

# Run schema creation
CREATE DATABASE IF NOT EXISTS optiinfra_metrics;
USE optiinfra_metrics;
```

Copy and paste the contents of `database/clickhouse/schemas/metrics.sql`

**Verify:**
```sql
SHOW TABLES;
-- Should show: cost_metrics, performance_metrics, resource_metrics, application_metrics

SELECT count() FROM cost_metrics;
-- Should return: 0 (empty table)
```

### PostgreSQL Schemas

```powershell
# Connect to PostgreSQL
docker exec -it optiinfra-postgres psql -U optiinfra -d optiinfra
```

Copy and paste the contents of `database/postgres/schemas/collection_history.sql`

**Verify:**
```sql
\dt
-- Should show: collection_history

SELECT COUNT(*) FROM collection_history;
-- Should return: 0
```

---

## Step 3: Build Data Collector Service

```powershell
# Build the Docker image
docker build -t optiinfra-data-collector:latest ./services/data-collector

# Expected: Successfully built and tagged
```

**Verify:**
```powershell
docker images | Select-String "data-collector"
```

---

## Step 4: Start Data Collector Service

```powershell
# Start data-collector service
docker-compose up -d data-collector

# Check logs
docker logs optiinfra-data-collector --tail 50
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8005
```

**Verify:**
```powershell
docker ps | Select-String "data-collector"
```

---

## Step 5: Test Health Endpoint

```powershell
# Test health check
curl http://localhost:8005/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "data-collector",
  "version": "0.1.0",
  "timestamp": "2025-10-29T...",
  "dependencies": {
    "clickhouse": "connected",
    "postgres": "connected",
    "redis": "connected"
  }
}
```

---

## Step 6: Test Collectors Status

```powershell
curl http://localhost:8005/api/v1/collectors/status
```

**Expected Response:**
```json
{
  "collectors": {
    "vultr": {
      "status": "active",
      "data_types": ["cost"],
      "last_collection": null,
      "phase": "6.1 - Implemented"
    },
    "aws": {
      "status": "placeholder",
      "data_types": ["cost"],
      "last_collection": null,
      "phase": "6.5 - To be implemented"
    },
    "gcp": {
      "status": "placeholder",
      "data_types": ["cost"],
      "last_collection": null,
      "phase": "6.5 - To be implemented"
    },
    "azure": {
      "status": "placeholder",
      "data_types": ["cost"],
      "last_collection": null,
      "phase": "6.5 - To be implemented"
    }
  },
  "summary": {
    "total_providers": 4,
    "active_providers": 1,
    "placeholder_providers": 3
  }
}
```

---

## Step 7: Test Vultr Collection (Manual Trigger)

**⚠️ Requires VULTR_API_KEY to be set**

```powershell
# Set your Vultr API key
$env:VULTR_API_KEY = "your_vultr_api_key_here"

# Restart data-collector with the API key
docker-compose up -d data-collector

# Trigger collection
curl -X POST http://localhost:8005/api/v1/collect/trigger `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "alpesh_chokshi",
    "provider": "vultr",
    "data_types": ["cost"]
  }'
```

**Expected Response:**
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "message": "Collection completed for vultr",
  "started_at": "2025-10-29T..."
}
```

**Check Logs:**
```powershell
docker logs optiinfra-data-collector --tail 100
```

**Expected Log Output:**
```
INFO: [task_id] Collection triggered for customer: alpesh_chokshi, provider: vultr
INFO: [task_id] Collecting cost data from vultr
INFO: Collected account costs: pending=$X.XX
INFO: Collected X invoices
INFO: Collected costs for X instances
INFO: [task_id] Wrote X cost metrics to ClickHouse
INFO: Wrote collection history record: X
INFO: Published data_updated event for alpesh_chokshi/vultr/cost
```

---

## Step 8: Verify Data in ClickHouse

```powershell
docker exec -it optiinfra-clickhouse clickhouse-client
```

```sql
USE optiinfra_metrics;

-- Check cost metrics
SELECT 
    customer_id,
    provider,
    cost_type,
    SUM(amount) as total_cost,
    COUNT(*) as record_count
FROM cost_metrics
GROUP BY customer_id, provider, cost_type;

-- View recent records
SELECT * FROM cost_metrics 
ORDER BY timestamp DESC 
LIMIT 10;
```

**Expected:** Should see records with your customer_id, provider=vultr, and cost data

---

## Step 9: Verify Data in PostgreSQL

```powershell
docker exec -it optiinfra-postgres psql -U optiinfra -d optiinfra
```

```sql
-- Check collection history
SELECT 
    customer_id,
    provider,
    task_id,
    status,
    metrics_collected,
    started_at,
    completed_at
FROM collection_history
ORDER BY started_at DESC
LIMIT 5;
```

**Expected:** Should see a record of your collection with status='success'

---

## Step 10: Verify Redis Events

```powershell
# Subscribe to Redis events
docker exec -it optiinfra-redis redis-cli

# Subscribe to data_updated channel
SUBSCRIBE data_updated

# In another terminal, trigger collection again
# You should see events published
```

**Expected Output:**
```
1) "message"
2) "data_updated"
3) "{\"event_type\":\"data_updated\",\"customer_id\":\"alpesh_chokshi\",\"provider\":\"vultr\",\"data_type\":\"cost\",\"records_count\":X,\"timestamp\":\"...\"}"
```

---

## Step 11: Error Handling Test

### Test with Invalid Provider
```powershell
curl -X POST http://localhost:8005/api/v1/collect/trigger `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "test",
    "provider": "invalid_provider",
    "data_types": ["cost"]
  }'
```

**Expected:** HTTP 400 with error message "Unsupported provider: invalid_provider"

### Test with Missing API Key
```powershell
# Remove VULTR_API_KEY and restart
docker-compose up -d data-collector

curl -X POST http://localhost:8005/api/v1/collect/trigger `
  -H "Content-Type: application/json" `
  -d '{
    "customer_id": "test",
    "provider": "vultr",
    "data_types": ["cost"]
  }'
```

**Expected:** HTTP 400 with error message "VULTR_API_KEY not configured"

---

## Step 12: Performance Test

```powershell
# Run multiple collections
for ($i=1; $i -le 5; $i++) {
    Write-Host "Collection $i"
    curl -X POST http://localhost:8005/api/v1/collect/trigger `
      -H "Content-Type: application/json" `
      -d "{\"customer_id\":\"test_$i\",\"provider\":\"vultr\",\"data_types\":[\"cost\"]}"
    Start-Sleep -Seconds 2
}
```

**Verify:**
- All collections complete successfully
- No memory leaks
- Database connections are properly closed

---

## Step 13: Integration Test

```powershell
# Full integration test script
cd services/data-collector

# Run all tests
pytest tests/ -v
```

---

## ✅ Validation Checklist

- [ ] Docker services started (postgres, clickhouse, redis)
- [ ] ClickHouse schemas created
- [ ] PostgreSQL schemas created
- [ ] Data-collector image built
- [ ] Data-collector service started
- [ ] Health endpoint responds
- [ ] Collectors status endpoint shows all 4 providers
- [ ] Vultr collection triggered successfully
- [ ] Data written to ClickHouse
- [ ] Collection history written to PostgreSQL
- [ ] Redis events published
- [ ] Error handling works correctly
- [ ] Performance test passed
- [ ] No errors in logs

---

## 🎯 Success Criteria

✅ **Service Running:** data-collector on port 8005  
✅ **Health Check:** Returns healthy status  
✅ **Vultr Collection:** Successfully collects and stores cost data  
✅ **ClickHouse:** Contains cost_metrics records  
✅ **PostgreSQL:** Contains collection_history records  
✅ **Redis:** Publishes data_updated events  
✅ **Error Handling:** Properly handles invalid inputs  
✅ **All 4 Providers:** Vultr active, AWS/GCP/Azure placeholders ready  

---

## 📝 Next Steps After Validation

1. **Phase 6.2** - Add Celery for scheduled collection
2. **Phase 6.3** - Refactor Cost Agent to read from ClickHouse
3. **Phase 6.4** - Implement Performance & Resource collectors
4. **Phase 6.5** - Implement AWS, GCP, Azure collectors

---

## 🆘 Troubleshooting

### Service won't start
```powershell
# Check logs
docker logs optiinfra-data-collector

# Check dependencies
docker ps | Select-String "postgres|clickhouse|redis"
```

### Can't connect to databases
```powershell
# Test connections
docker exec -it optiinfra-clickhouse clickhouse-client --query "SELECT 1"
docker exec -it optiinfra-postgres psql -U optiinfra -d optiinfra -c "SELECT 1"
docker exec -it optiinfra-redis redis-cli ping
```

### Collection fails
```powershell
# Verify API key
echo $env:VULTR_API_KEY

# Check Vultr API directly
curl -H "Authorization: Bearer $env:VULTR_API_KEY" https://api.vultr.com/v2/account
```

---

**Ready to validate! Start with Step 1 once Docker Desktop is running.** 🚀
