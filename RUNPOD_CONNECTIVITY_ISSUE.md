# 🔴 RunPod Connectivity Issue

## ❌ Problem Detected

Your local machine **cannot reach** the RunPod Prometheus at `http://213.173.105.12:9091`

**Error:** `The operation has timed out.`

---

## 🔍 Root Cause

The RunPod Prometheus port (9091) is **not accessible** from your local machine. This could be because:

1. **Port not exposed** in RunPod configuration
2. **Firewall blocking** the connection
3. **RunPod networking** doesn't allow external access to custom ports
4. **Services not running** on RunPod

---

## ✅ Solution Options

### **Option 1: Use RunPod's TCP Port Mapping (Recommended)**

RunPod provides TCP port mapping for exposing custom ports. You need to:

1. **In RunPod Console**, go to your pod settings
2. **Add TCP Port Mapping**:
   - Internal Port: `9091` (Prometheus)
   - External Port: Will be assigned by RunPod (e.g., `12345`)
3. **Get the external URL**: `tcp://213.173.105.12:12345`
4. **Update OptiInfra credentials** with the new URL

---

### **Option 2: Use RunPod's HTTP Proxy**

If RunPod doesn't support direct TCP access:

1. **Expose Prometheus via HTTP port** (usually port 80 or 443 is open)
2. **Use nginx reverse proxy** on RunPod to forward requests
3. **Access via**: `http://213.173.105.12/prometheus`

---

### **Option 3: Run OptiInfra Data Collector ON RunPod**

Instead of collecting from your local machine, run the data collector on RunPod itself:

1. **Deploy data-collector container** on RunPod
2. **Access Prometheus locally** (http://localhost:9091)
3. **Send data to your local OptiInfra** via webhook/API

---

## 🧪 Quick Test: Verify RunPod Connectivity

### **Test 1: Check if RunPod IP is reachable**

```powershell
Test-Connection -ComputerName 213.173.105.12 -Count 2
```

**Expected:** Should respond (ping successful)

---

### **Test 2: Check if port 9091 is open**

```powershell
Test-NetConnection -ComputerName 213.173.105.12 -Port 9091
```

**Expected:** `TcpTestSucceeded : True`

**If False:** Port is blocked or not exposed

---

### **Test 3: Try accessing from RunPod itself**

In your RunPod terminal:
```bash
curl http://localhost:9091/api/v1/query?query=up
```

**Expected:** JSON response with metrics

**This proves Prometheus is running, just not accessible externally**

---

## 🔧 Recommended Fix: Expose Prometheus via RunPod SSH Tunnel

### **Step 1: Create SSH Tunnel from Your Local Machine**

```powershell
# In PowerShell (keep this running)
ssh -L 9091:localhost:9091 root@213.173.105.12 -p 22
```

This creates a tunnel:
- Your `localhost:9091` → RunPod's `localhost:9091`

---

### **Step 2: Update OptiInfra Credentials**

```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    credential_name = "RunPod Live Demo"
    credentials = @{
        api_key = "your-runpod-api-key"
        prometheus_url = "http://localhost:9091"  # Now points to SSH tunnel
    }
    credential_type = "api_key"
    permissions = "read_only"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/credentials" -Method POST -Body $body -ContentType "application/json"
```

---

### **Step 3: Test the Tunnel**

```powershell
Invoke-WebRequest -Uri "http://localhost:9091/api/v1/query?query=up"
```

**Expected:** JSON response with Prometheus metrics

---

### **Step 4: Trigger Collection**

```powershell
$body = @{
    customer_id = "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"
    provider = "runpod"
    data_types = @("cost", "performance", "resource")
    async_mode = $false
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8005/api/v1/collect/trigger" -Method POST -Body $body -ContentType "application/json"
```

---

## 🎯 Alternative: Use RunPod's Exposed HTTP Port

RunPod typically exposes one HTTP port (e.g., port 8100 for vLLM). You can:

### **Option A: Expose Prometheus on a Different Port**

In your `docker-compose.yml` on RunPod:
```yaml
prometheus:
  ports:
    - "8200:9090"  # Use a different external port
```

Then access via: `http://213.173.105.12:8200`

---

### **Option B: Use vLLM's Metrics Endpoint**

vLLM exposes metrics at `http://213.173.105.12:8100/metrics`

This might already be accessible! Test:
```powershell
Invoke-WebRequest -Uri "http://213.173.105.12:8100/metrics"
```

If this works, you can configure OptiInfra to scrape directly from vLLM instead of Prometheus.

---

## 📋 What to Do Right Now

### **Immediate Action:**

1. **Test if vLLM port is accessible:**
   ```powershell
   Invoke-WebRequest -Uri "http://213.173.105.12:8100/health"
   ```

2. **If vLLM is accessible**, check its metrics:
   ```powershell
   Invoke-WebRequest -Uri "http://213.173.105.12:8100/metrics"
   ```

3. **In RunPod terminal**, verify Prometheus is running:
   ```bash
   curl http://localhost:9091/api/v1/query?query=up
   ```

4. **Check RunPod port mappings** in the RunPod console

---

## 🚀 Quick Win: Use SSH Tunnel (5 minutes)

**This is the fastest solution:**

1. Open a **new PowerShell window**
2. Run: `ssh root@213.173.105.12 -L 9091:localhost:9091`
3. Keep this window open
4. Update credentials to use `http://localhost:9091`
5. Run `.\monitor-runpod-workload.ps1` again

**This will work immediately!** 🎯

---

## 📊 What You'll See After Fix

Once connectivity is established:

### **Performance Metrics:**
- `vllm_request_duration_seconds` - Response latency
- `vllm_request_tokens_total` - Token throughput
- `vllm_num_requests_running` - Active requests

### **GPU Metrics:**
- `DCGM_FI_DEV_GPU_UTIL` - GPU utilization (should spike during 2 RPS phases)
- `DCGM_FI_DEV_MEM_COPY_UTIL` - Memory usage
- `DCGM_FI_DEV_GPU_TEMP` - Temperature

### **Workload Pattern Visible:**
```
Time    GPU Util    Requests
0-5m    80-90%      2 RPS (active)
5-10m   0-5%        0 RPS (rest)
10-20m  80-90%      2 RPS (active)
20-30m  0-5%        0 RPS (rest)
```

---

## 🎯 Summary

**Problem:** RunPod Prometheus not accessible from your local machine

**Best Solution:** SSH tunnel (5 minutes to set up)

**Alternative:** Expose Prometheus on RunPod's HTTP port

**Quick Test:** Try accessing vLLM metrics directly at port 8100

---

**Let's fix this and see your workload data!** 🚀
