# 🔍 OptiInfra Current Status - RunPod Demo

## ✅ What's Working

### **OptiInfra Services:**
- ✅ **Data Collector**: Running and healthy
- ✅ **ClickHouse**: Running
- ✅ **PostgreSQL**: Running
- ✅ **All 4 Agents**: Running
- ✅ **Portal UI**: Running (port 3001)
- ✅ **Dashboard API**: Working

### **RunPod Credentials:**
- ✅ **Configured**: Yes
- ✅ **Provider**: runpod
- ✅ **Status**: Active

### **Data Collection:**
- ⚠️ **Performance Metrics**: 0 records (not collected yet)
- ✅ **Cost Metrics**: 6 records (some data exists)
- ⚠️ **Resource Metrics**: 0 records (not collected yet)

---

## 🎯 Current Situation

### **What's Happening:**

1. **RunPod Demo is Running** (on RunPod server)
   - vLLM server serving Llama-3.1-8B
   - Prometheus collecting metrics
   - DCGM exporting GPU metrics

2. **OptiInfra is Ready** (on your local machine)
   - All services running
   - Credentials configured
   - Dashboard API working

3. **Missing Link: Data Collection**
   - OptiInfra has NOT yet collected data from RunPod
   - You need to trigger collection manually

---

## 🚀 What You Need to Do Next

### **Step 1: Get Your RunPod Prometheus URL**

In your RunPod terminal, run:
```bash
curl -s ifconfig.me
```

This gives you your RunPod IP (e.g., `213.173.105.12`)

Your Prometheus URL is: `http://YOUR_RUNPOD_IP:9091`

---

### **Step 2: Update RunPod Credentials with Prometheus URL**

On your local machine (PowerShell):
```powershell
$runpodIp = "YOUR_RUNPOD_IP"  # Replace with actual IP from Step 1

$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod Live Demo"
    credentials = @{
        api_key = "your-runpod-api-key"
        prometheus_url = "http://${runpodIp}:9091"
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json"
```

---

### **Step 3: Trigger Data Collection**

```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    data_types = @("cost", "performance", "resource")
    async_mode = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json"
```

**Expected Output:**
```json
{
  "status": "success",
  "message": "Collection completed",
  "metrics_collected": 150
}
```

---

### **Step 4: Verify Data Collection**

Run the verification script again:
```powershell
.\check-optiinfra.ps1
```

**You should now see:**
- ✅ Performance Metrics: 50+ records
- ✅ Cost Metrics: 10+ records
- ✅ Resource Metrics: 50+ records

---

### **Step 5: View Dashboard**

```powershell
Start-Process "http://localhost:3001/dashboard"
```

**You should see:**
- Cost trends showing RunPod spending
- GPU utilization charts
- Performance metrics (latency, throughput)
- Agent recommendations

---

## 🔍 How to Verify Everything is Working

### **Test 1: Check RunPod Prometheus is Accessible**

```powershell
$runpodIp = "YOUR_RUNPOD_IP"
Invoke-WebRequest -Uri "http://${runpodIp}:9091/api/v1/query?query=up"
```

**Expected:** JSON response with `"status":"success"`

---

### **Test 2: Check Data in ClickHouse**

```powershell
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT provider, metric_name, COUNT(*) FROM optiinfra_metrics.performance_metrics WHERE provider='runpod' GROUP BY provider, metric_name;"
```

**Expected:**
```
runpod  gpu_utilization     45
runpod  vllm_latency        45
runpod  throughput          45
```

---

### **Test 3: Check Dashboard API**

```powershell
$response = Invoke-WebRequest -Uri "http://localhost:8005/api/v1/dashboard?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11&provider=runpod"
$response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 3
```

**Expected:** JSON with cost_trends, performance_metrics, and summary data

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ RUNPOD SERVER                                           │
│                                                         │
│ vLLM (8100) → Prometheus (9091) ← DCGM (9401)         │
│                      ↓                                  │
│              Stores Metrics                             │
└─────────────────────────────────────────────────────────┘
                       ↓
                HTTP Request
                       ↓
┌─────────────────────────────────────────────────────────┐
│ YOUR LOCAL MACHINE (OptiInfra)                          │
│                                                         │
│ Data Collector (8005)                                   │
│      ↓ (fetches from Prometheus)                       │
│ ClickHouse                                              │
│      ↓ (stores metrics)                                 │
│ 4 AI Agents (8001-8004)                                │
│      ↓ (analyze data)                                   │
│ Dashboard API (8005)                                    │
│      ↓ (aggregates data)                                │
│ Portal UI (3001)                                        │
│      ↓ (displays to user)                               │
│ YOU SEE: Real-time RunPod metrics!                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🐛 Troubleshooting

### **If Collection Fails:**

1. **Check RunPod Prometheus is accessible:**
   ```powershell
   $runpodIp = "YOUR_IP"
   Invoke-WebRequest -Uri "http://${runpodIp}:9091/api/v1/query?query=up"
   ```

2. **Check Data Collector logs:**
   ```powershell
   docker logs optiinfra-data-collector --tail 50
   ```

3. **Verify credentials:**
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials/runpod?customer_id=a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
   ```

---

## ✅ Success Criteria

**Demo is successful when:**
1. ✅ RunPod Prometheus URL is accessible from your machine
2. ✅ OptiInfra credentials configured with correct Prometheus URL
3. ✅ Collection triggered successfully (metrics_collected > 0)
4. ✅ ClickHouse shows RunPod metrics (performance, cost, resource)
5. ✅ Dashboard API returns RunPod data
6. ✅ Portal UI displays RunPod metrics and agent recommendations

---

## 📞 Quick Commands Reference

```powershell
# Check OptiInfra status
.\check-optiinfra.ps1

# Trigger collection
$body = @{customer_id="a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11";provider="runpod";data_types=@("cost","performance","resource");async_mode=$false} | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json"

# View dashboard
Start-Process "http://localhost:3001/dashboard"

# Check ClickHouse data
docker exec optiinfra-clickhouse clickhouse-client --query "SELECT COUNT(*) FROM optiinfra_metrics.performance_metrics WHERE provider='runpod';"
```

---

**Current Status: ⚠️ Ready to Collect Data**

**Next Action: Update Prometheus URL and trigger collection!** 🚀
